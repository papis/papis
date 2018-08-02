import os
import papis
import papis.api
import papis.config
import papis.commands
import logging
import papis.cli


def run(
        verbose,
        config,
        lib,
        log,
        picktool,
        pick_lib,
        clear_cache,
        cores,
        set
    ):
    log_format = '%(levelname)s:%(name)s:%(message)s'
    if verbose:
        log = "DEBUG"
        log_format = '%(relativeCreated)d-'+log_format
    logging.basicConfig(
        level=getattr(logging, log),
        format=log_format
    )

    if len(set) == 0:
        for pair in set:
            papis.config.set(pair[0], pair[1])

    if config:
        papis.config.set_config_file(config)
        papis.config.reset_configuration()

    if picktool:
        papis.config.set("picktool", picktool)

    if pick_lib:
        lib = papis.api.pick(
            papis.api.get_libraries(),
            pick_config=dict(header_filter=lambda x: x)
        )

    papis.config.set_lib(lib)

    # Now the library should be set, let us check if there is a
    # local configuration file there, and if there is one, then
    # merge its contents
    local_config_file = os.path.expanduser(
        os.path.join(
            papis.config.get("dir"),
            papis.config.get("local-config-file")
        )
    )
    papis.config.merge_configuration_from_path(
        local_config_file,
        papis.config.get_configuration()
    )

    if clear_cache:
        papis.api.clear_lib_cache(lib)
