import math
import os.path

def get(data, name, trim=True):
    ret = data.split(name+':')[1].split('\n')[0]
    if trim:
        return ret.strip()
    return ret

def set(data, name, value):
    arr = data.split(name+':'+get(data, name, False))
    ret = arr[0] + name + ':' + value + arr[1]
    return ret

def get_timing(hit_data, timing_points):
    ret_timing_point = None
    for timing_point in timing_points:
        if timing_point[0] <= int(hit_data[2]):
            ret_timing_point = timing_point
    if ret_timing_point == None:
        ret_timing_point = timing_points[0]
    return ret_timing_point

def snap_to(num, bpm, snapping, offset):
    a = round(((num - offset) * snapping) / bpm)
    return math.floor((bpm * a) / snapping + offset)

def color_text(text, color=''):
    if color == 'ACCEPT':
        return f'\033[38;2;50;255;50m{text}\033[0m'
    if color == 'WARNING':
        return f'\033[38;2;255;150;50m{text}\033[0m'
    if color == 'ERROR':
        return f'\033[38;2;255;50;50m{text}\033[0m'
    else:
        return f'\033[38;2;255;255;255m{text}\033[0m'

def FLNDLS(songs_path, beatmapset_path, beatmap_name, p_index, p_max, harder=False):
    buff = '-'
    if harder:
        buff = '+'

    progress = color_text(f'({p_index}/{p_max}) {round(p_index/p_max * 100, 2)}% ')
    beatmap_path = f'{beatmapset_path}/{beatmap_name}'
    if not os.path.exists(beatmap_path):
        print(progress + color_text(f'Map not found: {beatmap_name}', 'ERROR'))
        return

    beatmap_data = open(beatmap_path, encoding='utf-8').read()

    mode = int(get(beatmap_data, 'Mode'))
    if mode != 3:
        print(progress + color_text(f'Map not mania: {beatmap_name}', 'ERROR'))
        return

    key_count = float(get(beatmap_data, 'CircleSize'))
    if key_count != 7:
        print(progress + color_text(f'Map not 7K: {beatmap_name}', 'ERROR'))
        return

    if beatmap_name.count('[') > 0:
        new_beatmap_name = f'{beatmap_name.split("[")[0]}[FLNDLS{buff}_{beatmap_name.split("[")[1]}'
    elif beatmap_name.count('(') > 0:
        new_beatmap_name = f'{beatmap_name.split("(")[-2]}[FLNDLS{buff}] ({beatmap_name.split("(")[-1]}'
    else:
        new_beatmap_name = f'{beatmap_name.split(".osu")[0]}_FLNDLS{buff}.osu'

    new_beatmap_path = f'{beatmapset_path}/{new_beatmap_name}'
    new_data = beatmap_data

    version = get(beatmap_data, 'Version')
    if f'FLNDLS+ | ' in version:
        print(progress + color_text(f'Map already FLNDLS+: {beatmap_name}', 'WARNING'))
        return
    if f'FLNDLS- | ' in version:
        print(progress + color_text(f'Map already FLNDLS-: {beatmap_name}', 'WARNING'))
        return

    new_version = f'FLNDLS{buff} | ' + version

    new_data = set(new_data, 'Version', new_version)

    # print(new_data)
    timing_points_ = new_data.split('[TimingPoints]')[1].split('[')[0].strip().split('\n')
    timing_points = []
    for timing_point in timing_points_:
        timing_data = timing_point.split(',')
        if len(timing_data) > 1 and float(timing_data[1]) >= 0:
            timing_points.append((float(timing_data[0]), float(timing_data[1])))

    hit_objects_ = new_data.split('[HitObjects]')[1].strip().split('\n')

    hit_objects = [[] for i in range(0, 7)]

    for hit_object in hit_objects_:
        hit_data = hit_object.split(',')
        key = max(min(math.floor((int(hit_data[0]) * 7) / 512), 6), 0)
        hit_objects[key].append(hit_object)

    new_data = new_data.split('[HitObjects]')[0]
    new_data += '[HitObjects]\n'
    changes = 0
    for key in range(0, 7):
        for i in range(0, len(hit_objects[key])):
            if i >= len(hit_objects[key]) - 1:
                new_data += hit_objects[key][i] + '\n'
                break
            c_hit_object = hit_objects[key][i]
            n_hit_object = hit_objects[key][i + 1]

            c_hit_data = c_hit_object.split(',')
            n_hit_data = n_hit_object.split(',')

            c_hit_data[5] = c_hit_data[5].split(':')
            n_hit_data[5] = n_hit_data[5].split(':')

            if c_hit_data[5][0].isnumeric():
                is_ln = int(c_hit_data[5][0]) > 0
            else:
                is_ln = False
            if harder or not is_ln:
                next_timing_point = get_timing(n_hit_data, timing_points)
                snap = round(next_timing_point[1]/4)

                hold_start = int(c_hit_data[2])

                hold_end = int(n_hit_data[2]) - snap
                if next_timing_point[1] > 1e+10:
                    print('No. Infinite BPM')
                    return
                hold_end = snap_to(hold_end, next_timing_point[1], 16, next_timing_point[0])
                if hold_end - hold_start > 0:
                    c_hit_data[5].insert(0, str(hold_end))
                    c_hit_data[3] = '128'
                    changes += 1

            c_hit_data[5] = ':'.join(c_hit_data[5])
            c_hit_object = ','.join(c_hit_data)
            new_data += c_hit_object + '\n'

    if changes == 0:
        print(progress + color_text(f'Map already Inverse{buff}: {beatmap_name}', 'WARNING'))
        return

    with open(new_beatmap_path, 'w', encoding='utf-8') as file:
        file.write(new_data)
    print(progress + color_text(f'Done (FLNDLS{buff}): {beatmap_name}', 'ACCEPT'))

def main():
    songs_path = 'C:/Users/anton/AppData/Local/osu!/Songs'
    beatmapsets = os.listdir(songs_path)
    index = 0
    beatmap_count = 0
    for beatmapset_name in beatmapsets:
        beatmapset_path = f'{songs_path}/{beatmapset_name}'
        if not os.path.exists(beatmapset_path):
            continue
        beatmaps = os.listdir(beatmapset_path)
        for beatmap_name in beatmaps:
            if not beatmap_name.endswith('.osu'):
                continue
            beatmap_count += 1
    for beatmapset_name in beatmapsets:
        beatmapset_path = f'{songs_path}/{beatmapset_name}'
        if not os.path.exists(beatmapset_path):
            continue
        beatmaps = os.listdir(beatmapset_path)
        for beatmap_name in beatmaps:
            if not beatmap_name.endswith('.osu'):
                continue
            index += 1
            FLNDLS(songs_path, beatmapset_path, beatmap_name, index, beatmap_count * 2, False)
            index += 1
            FLNDLS(songs_path, beatmapset_path, beatmap_name, index, beatmap_count * 2, True)

def single():
    songs_path = 'C:/Users/anton/AppData/Local/osu!/Songs'
    beatmapset_name = 'beatmap-638592658476932137-audio'
    beatmapset_path = f'{songs_path}/{beatmapset_name}'
    beatmaps = os.listdir(beatmapset_path)
    index = 0
    beatmap_count = 0
    for beatmap_name in beatmaps:
        if not beatmap_name.endswith('.osu'):
            continue
        beatmap_count += 1
    for beatmap_name in beatmaps:
        if not beatmap_name.endswith('.osu'):
            continue

        index += 1
        FLNDLS(songs_path, beatmapset_path, beatmap_name, index, beatmap_count * 2, False)
        index += 1
        FLNDLS(songs_path, beatmapset_path, beatmap_name, index, beatmap_count * 2, True)

main()
# single()
