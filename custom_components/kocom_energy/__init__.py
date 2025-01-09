import logging
import asyncio

from .const import DOMAIN, PLATFORMS


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})
    
    # options에서 update_interval을 가져와서 data에 병합
    if entry.options:
        data = {
            **entry.data,
            "update_interval": entry.options.get("update_interval", entry.data.get("update_interval", 3600))
        }
        hass.config_entries.async_update_entry(entry, data=data)
    
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # 설정 변경 지원
    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    return True

async def update_listener(hass, entry):
    """설정이 업데이트되면 호출됨"""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    """통합 구성요소 제거"""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
