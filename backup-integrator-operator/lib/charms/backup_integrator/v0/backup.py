"""TODO: Add a proper docstring here.

This is a placeholder docstring for this charm library. Docstrings are
presented on Charmhub and updated whenever you push a new version of the
library.

Complete documentation about creating and documenting libraries can be found
in the SDK docs at https://juju.is/docs/sdk/libraries.

See `charmcraft publish-lib` and `charmcraft fetch-lib` for details of how to
share and consume charm libraries. They serve to enhance collaboration
between charmers. Use a charmer's libraries for classes that handle
integration with their charm.

Bear in mind that new revisions of the different major API versions (v0, v1,
v2 etc) are maintained independently.  You can continue to update v0 and v1
after you have pushed v3.

Markdown is supported, following the CommonMark specification.
"""

import logging
from pathlib import Path
from typing import Optional, Union, List

import ops
from pydantic import BaseModel, field_validator, ConfigDict, field_serializer

# The unique Charmhub library identifier, never change it
LIBID = "55d94366e2624c1786227c24742c558f"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 1

DEFAULT_BACKUP_RELATION_NAME = "backup"

logger = logging.getLogger(__name__)


class BackupSpec(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda name: name.replace("_", "-"),
        serialize_by_alias=True,
        populate_by_name=True,
    )
    fileset: List[Path]
    run_before_backup: Optional[Path] = None
    run_after_backup: Optional[Path] = None
    run_before_restore: Optional[Path] = None
    run_after_restore: Optional[Path] = None

    @field_validator("fileset", mode="before")
    @classmethod
    def _coerce_fileset(cls, value: Union[str, List[str], List[Path]]) -> List[Path]:
        if isinstance(value, str):
            parts = [p.strip() for p in value.split(",") if p.strip()]
            return [Path(p) for p in parts]
        return [Path(p) for p in value]

    @field_validator("fileset", mode="after")
    @classmethod
    def _validate_fileset(cls, v: list[Path]) -> list[Path]:
        if not v:
            raise ValueError("fileset cannot be empty")
        for path in v:
            str_path = str(path)
            if str_path != str_path.strip():
                raise ValueError("path cannot start or end with whitespaces")
            if "," in str_path:
                raise ValueError("path cannot contain commas")
        if [str(p) for p in v if not p.is_absolute()]:
            raise ValueError(f"all path in fileset must be absolute.")
        return v

    @field_serializer("fileset", mode="plain")
    def _serialize_fileset(self, v: list[Path]) -> str:
        return ",".join(map(str, v))

    @field_validator(
        "run_before_backup",
        "run_after_backup",
        "run_before_restore",
        "run_after_restore",
        mode="before",
    )
    @classmethod
    def _coerce_optional_path(cls, v: Optional[Union[str, Path]]):
        if v is None:
            return v
        return Path(v)

    @field_validator(
        "run_before_backup",
        "run_after_backup",
        "run_before_restore",
        "run_after_restore",
        mode="after",
    )
    @classmethod
    def _validate_optional_path_absolute(cls, v: Optional[Path]) -> Optional[Path]:
        if v is None:
            return None
        if not v.is_absolute():
            raise ValueError("path must be absolute")
        return v

    @field_serializer(
        "run_before_backup",
        "run_after_backup",
        "run_before_restore",
        "run_after_restore",
        mode="plain",
    )
    def _serialize_optional_path(self, v: Optional[Path]) -> Optional[str]:
        if v is None:
            return None
        else:
            return str(v)


class BackupDynamicRequirer:
    def __init__(
        self,
        charm: ops.CharmBase,
        relation_name: str = DEFAULT_BACKUP_RELATION_NAME,
    ):
        self._charm = charm
        self._relation_name = relation_name

    def _request_backup(self, spec: BackupSpec):
        for relation in self._charm.model.relations[self._relation_name]:
            data = spec.model_dump(exclude_none=True)
            relation_data = relation.data[self._charm.app]
            if dict(relation_data) == data:
                continue
            relation_data.clear()
            logger.info("request backup with %s", data)
            relation_data.update(data)

    def request_backup(
        self,
        fileset: List[Union[str, Path]],
        run_before_backup: Optional[Union[str, Path]] = None,
        run_after_backup: Optional[Union[str, Path]] = None,
        run_before_restore: Optional[Union[str, Path]] = None,
        run_after_restore: Optional[Union[str, Path]] = None,
    ):
        spec = BackupSpec(
            fileset=fileset,
            run_before_backup=run_before_backup,
            run_after_backup=run_after_backup,
            run_before_restore=run_before_restore,
            run_after_restore=run_after_restore,
        )
        self._request_backup(spec)


class BackupRequirer:
    def __init__(
        self,
        charm: ops.CharmBase,
        *,
        fileset: List[Union[str, Path]],
        run_before_backup: Optional[Union[str, Path]] = None,
        run_after_backup: Optional[Union[str, Path]] = None,
        run_before_restore: Optional[Union[str, Path]] = None,
        run_after_restore: Optional[Union[str, Path]] = None,
        relation_name: str = DEFAULT_BACKUP_RELATION_NAME,
    ):
        self._charm = charm
        self._relation_name = relation_name
        self._spec = BackupSpec(
            fileset=fileset,
            run_before_backup=run_before_backup,
            run_after_backup=run_after_backup,
            run_before_restore=run_before_restore,
            run_after_restore=run_after_restore,
        )
        self._dynamic_requirer = BackupDynamicRequirer(charm=charm, relation_name=relation_name)
        self._listen_on_every_event()

    def _listen_on_every_event(self):
        for attr in dir(self._charm.on):
            event = getattr(self._charm.on, attr)
            if isinstance(event, ops.EventBase):
                continue
            self._charm.framework.observe(event, self._set_relation_data)

    def _set_relation_data(self, _: ops.EventBase):
        self._dynamic_requirer._request_backup(spec=self._spec)


class BackupProvider:
    def __init__(
        self,
        charm: ops.CharmBase,
        *,
        relation_name: str = DEFAULT_BACKUP_RELATION_NAME,
    ):
        self._charm = charm
        self._relation_name = relation_name

    def get_backup_spec(self, relation: ops.Relation) -> Optional[BackupSpec]:
        if relation.app is None:
            return None
        data = relation.data[relation.app]
        if not data:
            return None
        return BackupSpec.model_validate(data)
