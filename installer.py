import os
import zipfile
import urllib.request
from pathlib import Path

release_tag = "release"

def create_installer():
    print("Chrome Extension Installer")
    print("=" * 50)

    # Get extension URL or path
    extension_source = f"https://github.com/EunoiaC/Verify/releases/download/{release_tag}/installable-extension.zip"
    install_dir = input(f"\nEnter installation directory (default: current directory): ").strip()
    if not install_dir:
        install_dir = "."

    # Create installation directory
    install_path = Path(install_dir)
    install_path.mkdir(parents=True, exist_ok=True)

    # Download or copy extension files
    if extension_source.startswith(('http://', 'https://')):
        print(f"\nDownloading extension from {extension_source}...")
        zip_path = install_path / "extension.zip"
        urllib.request.urlretrieve(extension_source, zip_path)
    else:
        zip_path = Path(extension_source)

    # Extract extension files
    print("Extracting extension files...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(install_path)

    # Remove zip if downloaded
    if extension_source.startswith(('http://', 'https://')):
        zip_path.unlink()

    # delete __MACOSX folder if exists
    macosx_path = install_path / "__MACOSX"
    if macosx_path.exists() and macosx_path.is_dir():
        import shutil
        shutil.rmtree(macosx_path)
    print("Extension files extracted.")

    # Create .env file
    print("\n" + "=" * 50)
    print("API Configuration")
    print("=" * 50)

    gemini_api = input("\nEnter your GEMINI_API key: ").strip()
    google_search_api = input("Enter your GOOGLE_SEARCH_API key: ").strip()

    env_content = f'''GEMINI_API="{gemini_api}"
GOOGLE_SEARCH_API="{google_search_api}"
'''

    env_path = install_path / "installable-extension" / ".env"
    with open(env_path, 'w') as f:
        f.write(env_content)

    # go into install_path/installable-extension and install requirements.txt
    print("\nInstalling required Python packages...")
    # figure out if we need pip or pip3
    pip_command = 'pip3' if os.system('pip3 --version') == 0 else 'pip'

    os.system(f'{pip_command} install -r "{install_path / "installable-extension" / "requirements.txt"}"')

    print(f"\n✓ Installation complete!")
    print(f"✓ Extension files: {install_path.absolute()}")
    print(f"✓ Configuration: {env_path.absolute()}")
    print("\nTo load the extension in Chrome:")
    print("1. Open chrome://extensions/")
    print("2. Enable 'Developer mode'")
    print("3. Click 'Load unpacked'")
    print(f"4. Select the folder: {(install_path/"installable-extension").absolute()}")


if __name__ == "__main__":
    try:
        create_installer()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
