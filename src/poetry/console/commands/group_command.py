from __future__ import annotations

from typing import TYPE_CHECKING

from cleo.helpers import option

from poetry.console.commands.env_command import EnvCommand


if TYPE_CHECKING:
    from cleo.io.inputs.option import Option

    from poetry.packages.project_package import ProjectPackage


class GroupCommand(EnvCommand):
    @staticmethod
    def _group_dependency_options() -> list[Option]:
        return [
            option(
                "without",
                None,
                "The dependency groups to ignore for installation.",
                flag=False,
                multiple=True,
            ),
            option(
                "with",
                None,
                "The optional dependency groups to include for installation.",
                flag=False,
                multiple=True,
            ),
            option("default", None, "Only install the default dependencies."),
            option(
                "only",
                None,
                "The only dependency groups to install.",
                flag=False,
                multiple=True,
            ),
        ]

    @property
    def non_optional_groups(self) -> set[str]:
        # TODO: this should move into poetry-core
        return {
            group.name
            for group in self.poetry.package._dependency_groups.values()
            if not group.is_optional()
        }

    @property
    def activated_groups(self) -> set[str]:
        groups = {}

        for key in {"with", "without", "only"}:
            groups[key] = {
                group.strip()
                for groups in self.option(key)
                for group in groups.split(",")
            }

        if self.option("default"):
            groups["only"].add("default")

        for opt, new, group in [
            ("no-dev", "only", "default"),
            ("dev", "without", "default"),
            ("dev-only", "without", "default"),
        ]:
            if self.io.input.has_option(opt) and self.option(opt):
                self.line_error(
                    f"<warning>The `<fg=yellow;options=bold>--{opt}</>` option is"
                    f" deprecated, use the `<fg=yellow;options=bold>--{new} {group}</>`"
                    " notation instead.</warning>"
                )
                groups[new].add(group)

        return groups["only"] or self.non_optional_groups.union(
            groups["with"]
        ).difference(groups["without"])

    def project_with_activated_groups_only(self) -> ProjectPackage:
        return self.poetry.package.with_dependency_groups(
            list(self.activated_groups), only=True
        )