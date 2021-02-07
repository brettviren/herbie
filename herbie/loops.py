
def loop_dump(wm):
    for event in wm.events():
        print(event)
        parts = event.split('\t')
        if parts[0] == "reload":
            break
        
        

import time
from collections import defaultdict

def loop_switch(wm):
    '''
    Switch windows.  Assumes stamp loop also enabled
    '''
    delay = 2.0                 # seconds
    seq_last_time = 0
    seq_tag = None              # guard against fast tag switch
    sequence = list()

    for event in wm.events('switch_window|reload'):

        parts = event.split('\t')
        evt = parts[0]

        if evt == "reload":
            break

        in_sequence = True

        tag = wm.focused_tag
        if tag != seq_tag:
            in_sequence = False

        now = time.time()
        if now - seq_last_time > delay:
            in_sequence = False

        seq_last_time = now

        if in_sequence:
            seq_index = (seq_index+1)%len(sequence)
            wid = sequence[seq_index]
            wm(f"jumpto {wid}")
            continue

        # start sequence
        wids = wm.wids(tag)
        if len(wids) < 2:
            continue

        timed = list()
        for wid in wids:
            t = wm(f'attr clients.{wid}.my_focus_time')
            timed.append((float(t), wid))
        timed.sort()
        timed.reverse()
        sequence = [t[1] for t in timed]

        seq_index = 1;
        seq_tag = tag
        wid = sequence[seq_index]
        wm(f"jumpto {wid}")
        continue


def loop_stamp(wm):
    '''
    Set a focus_time attribute on windows and tags
    '''
    now = time.time()

    #print(f'start stamp loop {now}')

    # first, hit each tag and window to assure it has a my_focus_time
    # attribute set.
    for tagdot in wm("complete 1 attr tags.by-name.").split('\n'):
        tag = tagdot.split('.',1)[0].strip()
        if not tag:
            continue
        #print(f"tag {tag} my_focus_time")
        try:
            wm(f'new_attr string tags.by-name.{tag}.my_focus_time {now}')
        except RuntimeError:
            pass            # assume alread set
        
    clis = wm("complete 1 attr clients.")
    for cli in clis.split('\n'):
        parts = cli.strip().split('.')
        if len(parts) < 2:
            continue
        wid = parts[1].strip()
        if not wid.startswith('0x'):
            continue
        #print(f"window {wid} my_focus_time")
        try:
            wm(f'new_attr string clients.{wid}.my_focus_time {now}')
        except RuntimeError:
            pass            # assume alread set

    for event in wm.events('tag_changed|focus_changed|reload'):
        #print(f'loop stamp with event {event}')
        now = time.time()
        parts = event.split('\t')
        evt = parts[0]

        if evt == "reload":
            break

        if evt == "tag_changed":
            tag = parts[1]
            try:
                wm(f'set_attr tags.by-name.{tag}.my_focus_time {now}')
            except RuntimeError:
                pass

        if evt == "focus_changed":
            wid = parts[1]
            if wid == "0x0":
                continue
            try:
                wm(f'set_attr clients.{wid}.my_focus_time {now}')
            except RuntimeError:
                pass

def loop_stamp_switch(wm):
    # track tags of clients with timestamps
    clients = defaultdict(dict)

    delay = 2.0                 # seconds to stay in sequence
    seq_last_time = 0
    seq_last_event = None

    sequence = list()
    seq_index = None
    seq_tag = None

    for event in wm.events('focus_changed|switch_window|reload'):

        parts = event.split('\t')
        evt = parts[0]

        if evt == "reload":
            break

        tag = wm.focused_tag
        cli = wm('attr clients.focus.winid')

        now = time.time()
        in_sequence = True
        if tag != seq_tag:
            in_sequence = False
        if now - seq_last_time > delay:
            in_sequence = False
        if evt == 'focus_changed' and seq_last_event == 'focus_changed':
            in_sequence = False
        seq_last_time = now
        seq_last_event = evt

        #print (in_sequence, tag, cli, event)

        if in_sequence:

            if evt == 'switch_window': # advance window
                seq_index = (seq_index+1)%len(sequence)
                wid = sequence[seq_index]
                wm(f"jumpto {wid}")
                pass

            if evt == 'focus_changed': # ignore
                seq_changed = now
                continue

        else:                          # not in sequence

            if seq_tag:
                clients[seq_tag][sequence[seq_index]] = seq_changed
                seq_tag = None
                seq_index = None
                sequence = list()

            if evt == 'switch_window': # start sequence
                # merge any new wids with known wids
                wids = wm.wids(tag)
                have = set(wids)
                know = set(clients[tag])
                for new in have-know:
                    clients[tag][new] = time.time()
                for old in know-have:
                    clients[tag].pop(old)

                wids = [(v,k) for k,v in clients[tag].items()]

                if len(wids) < 2:
                    continue
                wids.sort()
                wids.reverse()
                sequence = [k for v,k in wids]
                seq_index = 1;
                seq_tag = tag
                wid = sequence[seq_index]
                wm(f"jumpto {wid}")
                continue

            if evt == 'focus_changed': # update time stamp
                clients[tag][cli] = now


