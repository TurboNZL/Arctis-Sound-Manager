"""With channels_enabled False (the fork default) no channel config is built
and audio is left alone; the WirePlumber quirks are not part of that path."""
import pytest

from arctis_sound_manager import sonar_to_pipewire as stp

pytestmark = pytest.mark.channels_off


def _settings_with(monkeypatch, value):
    class _GS:
        channels_enabled = value
    from arctis_sound_manager import settings
    monkeypatch.setattr(settings.GeneralSettings, "read_from_file",
                        classmethod(lambda cls: _GS()))


def test_default_is_off():
    from arctis_sound_manager.settings import GeneralSettings
    assert GeneralSettings.channels_enabled is False


def test_reads_the_setting(monkeypatch):
    _settings_with(monkeypatch, True)
    assert stp.channels_enabled() is True
    _settings_with(monkeypatch, False)
    assert stp.channels_enabled() is False


def test_repair_functions_do_nothing_when_off(monkeypatch):
    _settings_with(monkeypatch, False)
    assert stp.check_and_fix_stale_configs() == (False, False)
    assert stp.ensure_sonar_eq_configs() is False
    assert stp.apply_spatial_audio_change() is False
    assert stp.maybe_recover_from_safe_mode() is False
    assert stp.ensure_filter_chain_healthy() is True


def test_disable_moves_configs_aside_and_is_reversible(monkeypatch, tmp_path):
    conf = tmp_path / "filter-chain.conf.d"
    conf.mkdir()
    (conf / "sonar-game-eq.conf").write_text("x")
    (conf / "unrelated.conf").write_text("keep")
    monkeypatch.setattr(stp, "_CONF_DIR", conf)
    moved = stp.disable_channel_configs()
    assert moved == ["sonar-game-eq.conf"]
    assert not (conf / "sonar-game-eq.conf").exists()
    assert (conf / "unrelated.conf").read_text() == "keep"
    assert (tmp_path / "filter-chain.conf.d.channels-off" / "sonar-game-eq.conf").exists()


def test_channel_only_dep_prompts_are_dropped_when_off(monkeypatch):
    from arctis_sound_manager import system_deps_checker as sdc
    _settings_with(monkeypatch, False)
    names = {r.check.name for r in sdc.run_all_checks()}
    assert not names & sdc._CHANNEL_ONLY_CHECKS
    _settings_with(monkeypatch, True)
    names = {r.check.name for r in sdc.run_all_checks()}
    assert sdc._CHANNEL_ONLY_CHECKS <= names
