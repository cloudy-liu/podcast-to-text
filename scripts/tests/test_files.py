from podcast_to_text.files import episode_directory_name, safe_name


def test_safe_name_replaces_windows_invalid_characters():
    assert safe_name('142. 标题: A/B\\C?D*"E<篇>|') == "142. 标题- A-B-C-D-E-篇"


def test_episode_directory_name_defaults_to_title_and_short_episode_id():
    name = episode_directory_name(
        title="142. 雨森的创投观察第2集：Harness、下一个字节、2026大机会和Stanley Druckenmiller",
        episode_id="6a15a2cbff7b9a8c0a5b953f",
    )

    assert name == (
        "142. 雨森的创投观察第2集-Harness、下一个字节、2026大机会和Stanley "
        "Druckenmiller__6a15a2cb"
    )


def test_episode_directory_name_can_keep_legacy_episode_id_only():
    assert (
        episode_directory_name(
            title="节目标题",
            episode_id="6a15a2cbff7b9a8c0a5b953f",
            template="id",
        )
        == "6a15a2cbff7b9a8c0a5b953f"
    )


def test_episode_directory_name_can_use_title_only():
    assert (
        episode_directory_name(
            title="节目标题: 第二集",
            episode_id="6a15a2cbff7b9a8c0a5b953f",
            template="title",
        )
        == "节目标题- 第二集"
    )
