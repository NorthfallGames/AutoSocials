import argparse
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PROVIDERS_DIR = ROOT_DIR / "src" / "classes" / "providers"


def slug_to_class_prefix(slug: str) -> str:
    """Convert `my_provider` to `MyProvider`."""
    return "".join(part.capitalize() for part in slug.split("_") if part)


def validate_provider_slug(slug: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_]*", slug):
        raise ValueError(
            "Provider slug must match [a-z][a-z0-9_]* (example: linkedin, tiktok_bot)."
        )
    return slug


def validate_class_prefix(class_prefix: str) -> str:
    if not class_prefix.isidentifier():
        raise ValueError(
            "Class prefix must be a valid Python identifier (example: LinkedIn, TikTokBot)."
        )
    return class_prefix


def build_init_template(provider_slug: str, class_prefix: str) -> str:
    return (
        f"from classes.providers.{provider_slug}.controller import {class_prefix}MenuController\n"
        f"from classes.providers.{provider_slug}.service import {class_prefix}Service\n\n"
        f"__all__ = [\"{class_prefix}MenuController\", \"{class_prefix}Service\"]\n"
    )


def build_controller_template(
    provider_slug: str,
    class_prefix: str,
    display_name: str,
    service_name: str,
) -> str:
    menu_title = provider_slug.upper()
    return f'''from classes.account_menu import BaseAccountMenuController
from classes.providers.{provider_slug}.service import {class_prefix}Service
from constants import COMMON_ACCOUNT_FIELDS
from status import error, info, question, success
from art import print_banner


class {class_prefix}MenuController(BaseAccountMenuController):
    """
    {display_name}-specific menu controller built on the shared account flow.
    """

    def __init__(self) -> None:
        super().__init__(
            provider="{provider_slug}",
            service_name="{service_name}",
            account_fields=COMMON_ACCOUNT_FIELDS,
        )

    def _build_service(self, account: dict) -> {class_prefix}Service:
        return {class_prefix}Service(
            account_uuid=account["id"],
            account_nickname=account["nickname"],
            firefox_profile_path=account["firefox_profile"],
            niche=account["niche"],
        )

    def run_account_session(self, account: dict) -> None:
        try:
            service = self._build_service(account)
        except KeyError as exc:
            error(f"Missing required account field: {{exc}}")
            return
        except ValueError as exc:
            error(str(exc))
            return
        except Exception as exc:
            error(f"Failed to start {display_name} service: {{exc}}")
            return

        while True:
            print_banner()
            info("\\n============ {menu_title} OPTIONS ============", False)
            print(" 1. Test service")
            print(" 2. Generate video")
            print(" 3. Upload video")
            print(" 4. Show account details")
            print(" 5. Back")
            info("=========================================\\n", False)

            user_input = question("Select an option: ").strip().lower()

            if user_input in {{"5", "b", "back", "q", "quit"}}:
                info("Returning to account menu...")
                return

            print_banner()

            if user_input == "1":
                service.test_connection()

            elif user_input == "2":
                service.generate_video()

            elif user_input == "3":
                service.upload_video()

            elif user_input == "4":
                self._show_account_details(account)

            else:
                error("Invalid option selected.")

            question("\\nPress Enter to continue...", show_emoji=False)

    def _show_account_details(self, account: dict) -> None:
        success("{display_name} account details:")
        for key, value in account.items():
            success(f" - {{key}}: {{value}}", show_emoji=False)
'''


def build_service_template(display_name: str, class_prefix: str) -> str:
    return f'''from classes.providers.base_service import BaseProviderService
from status import info, success


class {class_prefix}Service(BaseProviderService):
    """
    Service class for {display_name} automation.

    This should contain the actual {display_name}-specific logic such as:
    - browser/session startup
    - content generation
    - metadata generation
    - upload flow
    - account-specific {display_name} actions
    """

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        firefox_profile_path: str,
        niche: str,
    ) -> None:
        """
        Initialise the {display_name} service.

        Args:
            account_uuid (str): Unique identifier for the account.
            account_nickname (str): Friendly name for the account.
            firefox_profile_path (str): Firefox profile path used for login/session.
            niche (str): Account niche/category.
        """
        super().__init__(
            account_uuid=account_uuid,
            account_nickname=account_nickname,
            firefox_profile_path=firefox_profile_path,
            niche=niche,
        )

    def test_connection(self) -> None:
        """
        Stub method to verify the service is wired correctly.
        """
        success("{display_name} service started successfully.")
        info(f"UUID: {{self.account_uuid}}", False)
        info(f"Nickname: {{self.account_nickname}}", False)
        info(f"Niche: {{self.niche}}", False)
        info(f"Firefox Profile: {{self.firefox_profile_path}}", False)

    def generate_video(self) -> None:
        """
        Stub for future video generation logic.
        """
        info("generate_video() is not implemented yet.")

    def upload_video(self) -> None:
        """
        Stub for future upload logic.
        """
        info("upload_video() is not implemented yet.")
'''


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(
            f"Refusing to overwrite existing file: {path}. Use --force to overwrite."
        )
    path.write_text(content, encoding="utf-8")


def create_provider_scaffold(
    provider_slug: str,
    class_prefix: str,
    display_name: str,
    service_name: str,
    force: bool,
) -> Path:
    provider_dir = PROVIDERS_DIR / provider_slug
    provider_dir.mkdir(parents=True, exist_ok=True)

    write_file(
        provider_dir / "__init__.py",
        build_init_template(provider_slug, class_prefix),
        force=force,
    )
    write_file(
        provider_dir / "controller.py",
        build_controller_template(provider_slug, class_prefix, display_name, service_name),
        force=force,
    )
    write_file(
        provider_dir / "service.py",
        build_service_template(display_name, class_prefix),
        force=force,
    )

    return provider_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a provider scaffold under src/classes/providers/<provider_slug>."
    )
    parser.add_argument(
        "provider_slug",
        help="Provider folder/module name in snake_case (example: linkedin).",
    )
    parser.add_argument(
        "--class-prefix",
        help="Class prefix in PascalCase (example: LinkedIn). Defaults to slug-derived name.",
    )
    parser.add_argument(
        "--display-name",
        help="Human-readable provider name (example: LinkedIn). Defaults to class prefix.",
    )
    parser.add_argument(
        "--service-name",
        help="Menu service label shown in the CLI. Defaults to '<display-name> Automater'.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffold files if they already exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        provider_slug = validate_provider_slug(args.provider_slug.strip().lower())
        class_prefix = validate_class_prefix(
            args.class_prefix.strip() if args.class_prefix else slug_to_class_prefix(provider_slug)
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    display_name = args.display_name.strip() if args.display_name else class_prefix
    service_name = args.service_name.strip() if args.service_name else f"{display_name} Automator"

    try:
        provider_dir = create_provider_scaffold(
            provider_slug=provider_slug,
            class_prefix=class_prefix,
            display_name=display_name,
            service_name=service_name,
            force=args.force,
        )
    except FileExistsError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Provider scaffold created at: {provider_dir}")
    print("Generated files: __init__.py, controller.py, service.py")
    print("Next: wire the new controller into src/main.py and update constants if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

