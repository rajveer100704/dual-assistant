#!/usr/bin/env python3
"""
deploy_hf.py — One-command HuggingFace Spaces deployment helper.

Usage:
  python deploy_hf.py --username YOUR_HF_USERNAME
  python deploy_hf.py --username YOUR_HF_USERNAME --space dual-assistant

What it does:
  1. Validates your HF token (from HF_TOKEN env var or ~/.cache/huggingface/token)
  2. Creates the Space if it doesn't exist (Streamlit SDK, CPU Basic)
  3. Copies README_HF.md → README.md for HF (HF reads README.md for the Space card)
  4. Pushes the repo via git
  5. Prints the live URL

Prerequisites:
  pip install huggingface_hub
  huggingface-cli login   # or set HF_TOKEN env var
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

_root = Path(__file__).parent


def run(cmd: str, check=True):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if check and result.returncode != 0:
        print(f"Error running: {cmd}")
        sys.exit(1)
    return result


def main():
    ap = argparse.ArgumentParser(description="Deploy to HuggingFace Spaces")
    ap.add_argument("--username", required=True, help="Your HuggingFace username")
    ap.add_argument("--space",    default="dual-assistant", help="Space name (default: dual-assistant)")
    ap.add_argument("--token",    default=os.getenv("HF_TOKEN", ""), help="HF API token (or set HF_TOKEN env)")
    args = ap.parse_args()

    repo_id = f"{args.username}/{args.space}"
    hf_url  = f"https://huggingface.co/spaces/{repo_id}"
    git_url = f"https://huggingface.co/spaces/{repo_id}"

    print(f"\n{'─'*55}")
    print(f"  Deploying to HuggingFace Spaces")
    print(f"  Repo: {repo_id}")
    print(f"  URL:  {hf_url}")
    print(f"{'─'*55}\n")

    # Step 1: Validate token
    try:
        from huggingface_hub import HfApi, create_repo, get_token
        token = args.token or get_token()
        api = HfApi(token=token)
        user = api.whoami()
        print(f"✅ Authenticated as: {user['name']}")
        if token:
            git_url = f"https://oauth:{token}@huggingface.co/spaces/{repo_id}"
    except ImportError:
        print("❌ huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)
    except Exception as e:
        print(f"❌ HF auth failed: {e}")
        print("   Run: huggingface-cli login  OR  set HF_TOKEN env var")
        sys.exit(1)

    # Step 2: Create Space if needed
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="streamlit",
            exist_ok=True,
            token=token,
        )
        print(f"✅ Space ready: {hf_url}")
    except Exception as e:
        print(f"⚠️  Space creation: {e} (may already exist)")

    # Step 3: Prepare README (HF reads README.md, not README_HF.md)
    hf_readme = _root / "README_HF.md"
    main_readme = _root / "README.md"
    backup_readme = _root / "README_github.md"

    if hf_readme.exists():
        shutil.copy(main_readme, backup_readme)
        shutil.copy(hf_readme, main_readme)
        print("✅ Swapped README.md → HF Space card")

    # Step 4: Git push
    print("\n📦 Pushing to HuggingFace Spaces...")
    remote_name = "hf_space"

    run(f'git remote remove {remote_name} 2>/dev/null || true', check=False)
    run(f'git remote add {remote_name} {git_url}')
    run(f'git add -A')
    run(f'git commit -m "Deploy to HF Spaces" --allow-empty')
    run(f'git push {remote_name} main --force')

    # Step 5: Restore README
    if backup_readme.exists():
        shutil.copy(backup_readme, main_readme)
        backup_readme.unlink()
        print("✅ Restored README.md for GitHub")

    print(f"""
{'═'*55}
  ✅ DEPLOYED SUCCESSFULLY

  Live URL:  {hf_url}
  
  Next steps:
  1. Open {hf_url}
  2. Go to Settings → Repository Secrets
  3. Add: GEMINI_API_KEY = AIzaSy-your-key-here
  4. Space will restart automatically
  
  Cold start: ~60-90s (OSS model download)
{'═'*55}
""")

    # Update README with the live URL
    readme = main_readme.read_text()
    placeholder = "https://huggingface.co/spaces/YOUR_USERNAME/dual-assistant"
    if placeholder in readme:
        readme = readme.replace(placeholder, hf_url)
        main_readme.write_text(readme)
        print(f"✅ README.md updated with live URL: {hf_url}")


if __name__ == "__main__":
    main()
