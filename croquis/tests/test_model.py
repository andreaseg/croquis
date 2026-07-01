import pytest

from croquis.model import (
    Category,
    Config,
    ImageSet,
    Mode,
    imagesets_matching_category,
    load_config,
    merge_imagesets,
    replace_config_fields,
    save_config,
)


def make_config():
    return Config(
        dimensions="800x600",
        imageset={
            "a": {"tags": ["male", "figure"], "paths": ["images/a"]},
            "b": {"tags": ["female", "figure"], "paths": ["images/b"]},
            "c": {"tags": ["hands"], "paths": ["images/c"]},
        },
        mode={
            "Classic": {"timers": "3*30s 1m", "default": "True"},
            "Classroom": {"manual": "True"},
        },
        category={"Figure": {"tags": ["figure"]}},
    )


def test_save_load_round_trip(tmp_path):
    config = make_config()
    path = str(tmp_path / "config.toml")

    save_config(config, path)
    loaded = load_config(path)

    assert loaded == config


def test_imagesets_matching_category_superset_match():
    config = make_config()
    matches = imagesets_matching_category(config.imageset, config.category["Figure"])
    assert set(matches.keys()) == {"a", "b"}


def test_imagesets_matching_category_no_match():
    config = make_config()
    matches = imagesets_matching_category(
        config.imageset, Category(tags=["nonexistent"])
    )
    assert matches == {}


def test_imagesets_matching_category_empty_tags_matches_everything():
    config = make_config()
    matches = imagesets_matching_category(config.imageset, Category(tags=[]))
    assert set(matches.keys()) == {"a", "b", "c"}


def test_merge_imagesets_unions_tags_and_paths():
    merged = merge_imagesets(
        [
            ImageSet(tags=["male", "figure"], paths=["images/a"]),
            ImageSet(tags=["female", "figure"], paths=["images/b"]),
        ]
    )
    assert sorted(merged.tags) == ["female", "figure", "male"]
    assert sorted(merged.paths) == ["images/a", "images/b"]


def test_merge_imagesets_single_imageset_is_identity():
    imageset = ImageSet(tags=["hands"], paths=["images/c"])
    merged = merge_imagesets([imageset])
    assert sorted(merged.tags) == sorted(imageset.tags)
    assert sorted(merged.paths) == sorted(imageset.paths)


def test_merge_imagesets_empty_returns_empty_imageset():
    merged = merge_imagesets([])
    assert merged == ImageSet(tags=[], paths=[])


def test_replace_config_fields_mutates_target_in_place():
    target = make_config()
    source = make_config()
    source.dimensions = "1024x768"
    source.imageset["d"] = ImageSet(tags=["new"], paths=["images/d"])

    replace_config_fields(target, source)

    assert target.dimensions == "1024x768"
    assert "d" in target.imageset


def test_mode_get_label_raises_without_manual_or_timers():
    mode = Mode(timers="", default=False, manual=False)
    with pytest.raises(ValueError):
        mode.get_label()


def test_mode_get_label_translates_header():
    mode = Mode(timers="", default=False, manual=True)
    header, body, _total = mode.get_label("ja")
    assert header == "手動"


def test_keybindings_and_excluded_images_round_trip(tmp_path):
    config = make_config()
    config.keybindings = {"menu": "Escape", "prev": "a", "next": "d"}
    config.excluded_images = ["c:\\images\\a\\1.jpg"]
    path = str(tmp_path / "config.toml")

    save_config(config, path)
    loaded = load_config(path)

    assert loaded == config


def test_config_loads_with_defaults_when_keybindings_and_excluded_images_missing():
    config = make_config()
    data = {
        "dimensions": config.dimensions,
        "imageset": {
            name: {"tags": imageset.tags, "paths": imageset.paths}
            for name, imageset in config.imageset.items()
        },
        "mode": {
            name: {"timers": mode.timers, "default": mode.default, "manual": mode.manual}
            for name, mode in config.mode.items()
        },
        "category": {
            name: {"tags": category.tags} for name, category in config.category.items()
        },
    }

    loaded = Config(**data)

    assert loaded.keybindings == {"menu": "Escape", "prev": "Left", "next": "Right"}
    assert loaded.excluded_images == []
    assert loaded.zen_mode is False
    assert loaded.theme == "auto"
    assert loaded.language == "en"
    assert loaded.monochrome_default is False


def test_zen_mode_round_trips(tmp_path):
    config = make_config()
    config.zen_mode = True
    path = str(tmp_path / "config.toml")

    save_config(config, path)
    loaded = load_config(path)

    assert loaded == config
    assert loaded.zen_mode is True


def test_theme_round_trips(tmp_path):
    config = make_config()
    config.theme = "dark"
    path = str(tmp_path / "config.toml")

    save_config(config, path)
    loaded = load_config(path)

    assert loaded == config
    assert loaded.theme == "dark"


def test_language_round_trips(tmp_path):
    config = make_config()
    config.language = "ja"
    path = str(tmp_path / "config.toml")

    save_config(config, path)
    loaded = load_config(path)

    assert loaded == config
    assert loaded.language == "ja"


def test_monochrome_default_round_trips(tmp_path):
    config = make_config()
    config.monochrome_default = True
    path = str(tmp_path / "config.toml")

    save_config(config, path)
    loaded = load_config(path)

    assert loaded == config
    assert loaded.monochrome_default is True
