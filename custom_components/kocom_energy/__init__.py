import logging
import asyncio

from .const import DOMAIN, PLATFORMS


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})

    # 사용자 입력 데이터 전달
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # 센서 외 다른 플랫폼을 사용할 경우를 위해 작업
    await hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )
    
    return True

# async def async_unload_entry(hass, entry):
#     """컴포넌트 삭제 시 관련 센서 삭제"""
#     unload_ok = all(
#         await asyncio.gather(
#             *[
#                 hass.config_entries.async_forward_entry_unload(entry, platform)
#                 for platform in PLATFORMS
#             ]
#         )
#     )

#     if unload_ok:
#         # 필요 시 컴포넌트와 관련된 추가적인 리소스를 정리하는 코드 추가
#         hass.data[DOMAIN].pop(entry.entry_id)

#     return unload_ok
