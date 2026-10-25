from worlds.LauncherComponents import Component, Type, components, launch


def run_client(*args: str) -> None:
    from .client import main

    launch(main, name="Pokemon Channel Client", args=args)


components.append(
    Component(
        "Pokemon Channel Client",
        func=run_client,
        game_name="Pokemon Channel",
        component_type=Type.CLIENT,
        supports_uri=True,
    )
)
