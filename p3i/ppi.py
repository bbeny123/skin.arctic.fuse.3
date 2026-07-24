import xbmc
import xbmcgui

GAMUT_MAP = {
    'default': '',
    'BT.2020nc': 'BT.2020',
    'Adobe_RGB': 'Adobe RGB',
    'Adobe_YCC601': 'Adobe YCC-601',
    'xvYCC709': 'xvYCC-709',
    'xvYCC601': 'xvYCC-601',
    'sYCC601': 'sYCC-601'
}


def main():
    monitor = xbmc.Monitor()
    home_window = xbmcgui.Window(10000)

    get_property = home_window.getProperty
    set_property = home_window.setProperty
    get_info = xbmc.getInfoLabel
    wait_for_abort = monitor.waitForAbort

    tick_1s = 0

    last_fps_raw = last_low_raw = last_disp_raw = last_eotf_raw = last_l5_raw = last_low_clean = None
    last_fps_out = ''

    while get_property("P3I_PPI_Active") and not monitor.abortRequested():

        # ==========================================================================================
        # PROP 1: AML FPS (Input - Output -> Dropped Frames)
        # ==========================================================================================
        out_changed = False
        fps = get_info('Player.Process(amlogic.video.fps.info)')
        if len(fps) >= 15:
            fps = fps[0:15]

            if fps != last_fps_raw:
                last_fps_raw = fps

                fps_in = fps[0:3].lstrip('0') or '0'
                fps_out = fps[6:9].lstrip('0') or '0'
                fps_drop = fps[12:15].lstrip('0') or '0'

                if fps_out != last_fps_out:
                    last_fps_out = fps_out
                    out_changed = True

                set_property(
                    "P3I_PPI_FPS",
                    f"{fps_in} - {fps_drop} -> {fps_out}"
                )

        # ==========================================================================================
        # PROP 2: 3-Sec Rolling Lowest Output AML FPS (Fallback to stable output FPS)
        # ==========================================================================================
        low = get_info('Player.Process(amlogic.video.fps.drop)')
        if (low != last_low_raw) or (not low and out_changed):
            last_low_raw = low

            if low:
                low = low.lstrip('0') or '0'
            else:
                low = last_fps_out

            if low != last_low_clean:
                last_low_clean = low

                set_property("P3I_PPI_FPS_Low", low)

        if not tick_1s:
            tick_1s = 10

            # ======================================================================================
            # PROP 3: Display Resolution & Refresh Rate (Throttled: 1000ms)
            # ======================================================================================
            disp = get_info('Player.Process(amlogic.displaymode)')
            if disp != last_disp_raw:
                last_disp_raw = disp

                if disp and disp != "unknown":
                    if ' ' in disp:
                        res_part, hz_part = disp.split(' ', 1)

                        if res_part[-1] == 'p': res_part = res_part[:-1]
                        if hz_part[-2:] == 'Hz': hz_part = hz_part[:-2] + ' Hz'

                        disp = f"{res_part} • {hz_part}"

                    elif disp[-1] == 'p':
                        disp = disp[:-1]

                    elif disp[-2:] == 'Hz':
                        disp = disp[:-2] + ' Hz'

                else:
                    disp = ""

                set_property("P3I_PPI_Display", disp)

            # ======================================================================================
            # PROP 4: Output EOTF & Gamut (Throttled: 1000ms)
            # ======================================================================================
            eotf = get_info('Player.Process(amlogic.eoft_gamut)')
            if eotf != last_eotf_raw:
                last_eotf_raw = eotf

                if eotf and eotf != "unknown":
                    eotf, _, gamut = eotf.partition(' ')
                    gamut = GAMUT_MAP.get(gamut, gamut)

                    eotf = f"{eotf} {gamut}".strip()
                else:
                    eotf = ""

                set_property("P3I_PPI_Output_EOTF", eotf)

            # ======================================================================================
            # PROP 5: Dolby Vision L5 Offsets (Throttled: 1000ms)
            # ======================================================================================
            if get_info('Player.Process(video.dovi.has.l5)') == '1':
                l5_t = get_info('Player.Process(video.dovi.l5.top.offset)') or '0'
                l5_b = get_info('Player.Process(video.dovi.l5.bottom.offset)') or '0'
                l5_l = get_info('Player.Process(video.dovi.l5.left.offset)') or '0'
                l5_r = get_info('Player.Process(video.dovi.l5.right.offset)') or '0'

                l5 = f"{l5_t} {l5_b} {l5_l} {l5_r}"

                if l5 != last_l5_raw:
                    last_l5_raw = l5

                    if l5_t == '0' and l5_b == '0':
                        l5 = f"[COLOR dialog_fg_70]↑ 0 | 0 ↓[/COLOR]"
                    else:
                        l5 = f"↑ {l5_t} | {l5_b} ↓"

                    total_digits = len(l5_t) + len(l5_b) + len(l5_l) + len(l5_r)
                    space_count = 2 if total_digits > 13 else (14 - total_digits)
                    l5 += ' ' * space_count

                    if l5_l == '0' and l5_r == '0':
                        l5 += f"[COLOR dialog_fg_70]← 0 | 0 →[/COLOR]"
                    else:
                        l5 += f"← {l5_l} | {l5_r} →"

                    set_property("P3I_PPI_L5", l5)

        tick_1s -= 1

        if wait_for_abort(0.1):
            break

    home_window.clearProperty("P3I_PPI_FPS")
    home_window.clearProperty("P3I_PPI_FPS_Low")
    home_window.clearProperty("P3I_PPI_Display")
    home_window.clearProperty("P3I_PPI_L5")
    home_window.clearProperty("P3I_PPI_Output_EOTF")


if __name__ == "__main__":
    main()
