import os
import shutil
import asyncio

async def clone_repository(github_url: str, dest_dir: str, access_token: str | None = None) -> str:
    """Clones a GitHub repository to a local directory."""
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    
    # Ensure parent dir exists
    os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
        
    clone_url = github_url
    if access_token:
        # Inject OAuth token if provided
        if github_url.startswith("https://"):
            clone_url = github_url.replace("https://", f"https://oauth2:{access_token}@")
            
    # Run git clone --depth 1 to save time
    process = await asyncio.create_subprocess_exec(
        "git", "clone", "--depth", "1", clone_url, dest_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_msg = stderr.decode()
        # Clean up URL in error message to avoid logging tokens
        if access_token:
            error_msg = error_msg.replace(access_token, "***")
        raise RuntimeError(f"Git clone failed: {error_msg}")
        
    return dest_dir
