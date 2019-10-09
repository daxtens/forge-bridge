import requests
import os
import time
import sys
from typing import Optional

PATCHWORK_INSTANCE = "https://patchwork.ozlabs.org/api/1.1/"
PROJECT = 'linuxppc-dev'
GIT_PULL_REMOTE = 'powerpc'
GIT_PULL_BRANCH = 'merge'
GIT_PUSH_REMOTE = 'dja'


def apply_series(series: dict) -> None:
    print("fetching mbox for", series['id'])
    mbox = requests.get(series['mbox'])
    if mbox.status_code != 200:
        print("couldn't fetch mbox")

    name = series['name']
    name = name.replace(' ', '_')
    for delc in "()[]{}!@#$%^&*;:'\"?\\|+=-<>":
        name = name.replace(delc, '')

    with open('mboxfile', 'wb') as f:
        f.write(mbox.content)
    print(f'wrote {name} to "mboxfile"')

    print(f'fetch - git -C linux fetch {GIT_PULL_REMOTE}')
    if not os.system(f"git -C linux fetch {GIT_PULL_REMOTE}") == 0:
        print("error fetching remote, aborting")
        sys.exit(1)

    print(f'checkout - git -C linux checkout -b {name} {GIT_PULL_REMOTE}/{GIT_PULL_BRANCH}')
    if not os.system(f"git -C linux checkout -b {name} {GIT_PULL_REMOTE}/{GIT_PULL_BRANCH}") == 0:
        print("could not checkout new branch, aborting")
        sys.exit(1)

    print('apply - git -C linux am $(pwd)/mboxfile')
    if not os.system("git -C linux am $(pwd)/mboxfile") == 0:
        print("git am failed, cleaning up")
        os.system("git -C linux am --abort")
    else:
        print(f'push - git -C linux push -f {GIT_PUSH_REMOTE} {name}')
        if not os.system(f'git -C linux push -f {GIT_PUSH_REMOTE} {name}') == 0:
            print("failed to push, aborting")
            sys.exit(1)

    print(f'cleanup - git -C linux checkout {GIT_PULL_BRANCH}; git -C linux branch -D {name}')
    os.system(f'git -C linux checkout {GIT_PULL_BRANCH}')
    os.system(f'git -C linux branch -D {name}')
    print('done')


def check_and_apply_events(last_event: Optional[int]) -> int:
    print("Fetching events")
    events = requests.get(PATCHWORK_INSTANCE + 'events/?category=series-completed&project=' + PROJECT)

    if events.status_code != 200:
        print("Events not fetched successfully")
        sys.exit(1)

    print("Got events")
    for event in events.json():
        event_id = int(event['id'])
        if not last_event or event_id > last_event:
            print("Processing", event_id)
            print("Series is", event['payload']['series']['id'])
            apply_series(event['payload']['series'])

    return events.json()[0]['id']


if __name__ == '__main__':
    try:
        with open('last_event', 'r') as f:
            last_event = int(f.read())
    except:
        last_event = None

    while True:
        last_event = check_and_apply_events(last_event)
        print("handled events up to", last_event)
        with open('last_event', 'w') as f:
            f.write(str(last_event))
        print("sleeping")
        time.sleep(60)