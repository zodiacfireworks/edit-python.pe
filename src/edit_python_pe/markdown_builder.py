import hashlib
import os
import re
from datetime import date, datetime
from typing import TYPE_CHECKING, cast

from .constants import BLOG_DIR, MEMBERS_DIR
from .file_io import _read_file, _write_file
from .strings import MD_CONTENT, _

if TYPE_CHECKING:
    from .app import MemberApp
    from .screens.member_form import MemberFormScreen


def _compute_file_name(
    aliases: list[str],
    name: str,
    email: str,
) -> str:
    if aliases:
        alias_for_name = aliases[0].lower().replace(" ", "_")
    else:
        alias_for_name = name.lower().replace(" ", "_")

    sha_hash = hashlib.sha256(
        (alias_for_name + email + datetime.now().isoformat()).encode("utf-8")
    ).hexdigest()[:8]
    return f"{alias_for_name}-{sha_hash}.md"


def _create_member_file(
    file_content: str,
    current_file: str | None,
    repo_path: str,
    aliases: list[str],
    name: str,
    email: str,
) -> tuple[str, str]:
    name_file = (
        current_file
        if current_file is not None
        else _compute_file_name(aliases, name, email)
    )

    file_path = os.path.join(repo_path, BLOG_DIR, MEMBERS_DIR, name_file)
    _write_file(file_content, file_path)
    return name_file, file_path


def load_file_into_form(
    screen: MemberFormScreen,
    filename: str,
) -> None:
    member_app = cast("MemberApp", screen.app)
    path_md = os.path.join(
        member_app.repo_path,
        BLOG_DIR,
        MEMBERS_DIR,
        filename,
    )

    if not os.path.exists(path_md):
        return
    try:
        content = _read_file(path_md)
    except Exception as e:
        member_app.exit(
            message=_("Error reading file {filename}: {error}").format(
                filename=filename, error=e
            )
        )
        return

    # Extract YAML frontmatter
    yaml_match = re.search(r"---\n(.*?)---\n", content, re.DOTALL)
    yaml_data = {}

    if yaml_match:
        try:
            import yaml

            yaml_data = yaml.safe_load(yaml_match.group(1))
        except Exception:
            yaml_data = {}

        if not isinstance(yaml_data, dict):
            yaml_data = {}

    screen.name_input.value = yaml_data.get("author", "")
    screen.city_input.value = yaml_data.get("location", "")

    # 1. Parse name and gravatar email
    name_match = re.search(
        r"^#\s+(.+)$",
        content,
        re.MULTILINE,
    )

    if name_match:
        screen.name_input.value = name_match.group(1).strip()

    gravatar_match = re.search(
        r"```\{gravatar\}\s+(.+)$",
        content,
        re.MULTILINE,
    )

    if gravatar_match:
        screen.email_input.value = gravatar_match.group(1).strip()

    # 2. Parse social networks from raw html block
    social_block_match = re.search(
        r"```\{raw\} html\n(.*?)\n```",
        content,
        re.MULTILINE | re.DOTALL,
    )

    if social_block_match:
        social_html = social_block_match.group(1)
        # Find all iconify-icon elements
        for match in re.finditer(
            r'<a\s+[^>]*href="([^"]+)"[^>]*>'
            r'\s*<iconify-icon\s+icon="simple-icons:([^"]+)"',
            social_html,
        ):
            url = match.group(1)
            platform = match.group(2)
            screen.add_social_entry(platform)
            last_entry = screen.social_entries[-1]
            last_entry.url_input.value = url

    # 3. Parse Aliases
    alias_match = re.search(
        r"^:Aliases:\s+(.+)$",
        content,
        re.MULTILINE,
    )

    if alias_match:
        aliases_str = alias_match.group(1)
        for alias_val in [a.strip() for a in aliases_str.split(",")]:
            screen.add_alias_entry()
            screen.alias_entries[-1].alias_input.value = alias_val

    # 4. Parse Ciudad and Homepage
    city_match = re.search(
        r"^:Ciudad:\s+(.+)$",
        content,
        re.MULTILINE,
    )

    if city_match:
        screen.city_input.value = city_match.group(1).strip()

    homepage_match = re.search(
        r"^:Homepage:\s+(.+)$",
        content,
        re.MULTILINE,
    )

    if homepage_match:
        screen.homepage_input.value = homepage_match.group(1).strip()

    # 5. Parse Text Areas
    who_match = re.search(
        r"^###? ¿Quién eres.*?\?\s*\n(.*?)(?=\n###? |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )

    if who_match:
        screen.who_area.text = who_match.group(1).strip()

    python_match = re.search(
        r"^###? ¿Cómo programas en Python.*?\?\s*\n(.*?)(?=\n###? |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )

    if python_match:
        screen.python_area.text = python_match.group(1).strip()

    contrib_match = re.search(
        r"^###? ¿Tienes alg[úu]n.*? a la comunidad de Python.*?\?\s*\n"
        r"(.*?)(?=\n###? |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )

    if contrib_match:
        screen.contributions_area.text = contrib_match.group(1).strip()

    avail_match = re.search(
        r"^###? ¿Estás.*?mentor.*?consultor.*?charlas.*?\?"
        r"\s*\n(.*?)(?=\n###? |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )

    if avail_match:
        screen.availability_area.text = avail_match.group(1).strip()


def build_md_content(
    name: str,
    email: str,
    aliases: list[str],
    socials: list[tuple[str, str]],
    city: str,
    homepage: str,
    who: str,
    python_: str,
    contributions: str,
    availability: str,
) -> str:
    alias = aliases[0] if aliases else name
    md_lines = [
        MD_CONTENT["yaml_start"],
        MD_CONTENT["yaml_blogpost"],
        MD_CONTENT["yaml_date"].format(date=date.today().strftime("%d %b, %Y")),
        MD_CONTENT["yaml_author"].format(author=alias),
        MD_CONTENT["yaml_location"].format(city=city),
        MD_CONTENT["yaml_category"],
        MD_CONTENT["yaml_language"],
        MD_CONTENT["yaml_image"],
        MD_CONTENT["yaml_excerpt"],
        MD_CONTENT["yaml_end"],
        "",
        MD_CONTENT["header_name"].format(name=name),
        "",
        MD_CONTENT["gravatar_block"].format(email=email),
        "",
    ]
    if socials:
        md_lines.append(MD_CONTENT["social_block_start"])
        md_lines.append(MD_CONTENT["social_ul_start"])
        for plat, url in socials:
            md_lines.append(MD_CONTENT["social_li"].format(platform=plat, url=url))
        md_lines.append(MD_CONTENT["social_ul_end"])
        md_lines.append(MD_CONTENT["social_block_end"])
        md_lines.append("")

    if aliases:
        md_lines.append(MD_CONTENT["aliases"].format(aliases=", ".join(aliases)))
        md_lines.append("")

    if city:
        md_lines.append(MD_CONTENT["city"].format(city=city))
        md_lines.append("")

    if homepage:
        md_lines.append(MD_CONTENT["homepage"].format(homepage=homepage))
        md_lines.append("")

    md_lines.append(MD_CONTENT["section_about"])
    md_lines.append("")

    if who:
        md_lines.append(MD_CONTENT["section_who"])
        md_lines.append("")
        md_lines.append(who)
        md_lines.append("")

    if python_:
        md_lines.append(MD_CONTENT["section_python"])
        md_lines.append("")
        md_lines.append(python_)
        md_lines.append("")

    if contributions:
        md_lines.append(MD_CONTENT["section_contrib"])
        md_lines.append("")
        md_lines.append(contributions)
        md_lines.append("")

    if availability:
        md_lines.append(MD_CONTENT["section_avail"])
        md_lines.append("")
        md_lines.append(availability)
        md_lines.append("")

    return "\n".join(md_lines)
