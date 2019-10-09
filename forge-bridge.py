import requests
import os
import time
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
    for delc in "()[]{}!@#$%^&*;:'\"?\\|+=":
        name = name.replace(delc, '')

    with open('mboxfile', 'wb') as f:
        f.write(mbox.content)
    print(f'wrote {name} to "mboxfile"')

    print(f'fetch - git -C linux fetch {GIT_PULL_REMOTE}')
    os.system(f"git -C linux fetch {GIT_PULL_REMOTE}")
    print(f'checkout - git -C linux checkout -b {name} {GIT_PULL_REMOTE}/{GIT_PULL_BRANCH}')
    os.system(f"git -C linux checkout -b {name} {GIT_PULL_REMOTE}/{GIT_PULL_BRANCH}")
    print('apply - git -C linux am $(pwd)/mboxfile')
    os.system("git -C linux am $(pwd)/mboxfile")
    print(f'push - git -C linux push {GIT_PUSH_REMOTE} {name}')
    os.system(f'git -C linux push {GIT_PUSH_REMOTE} {name}')
    print(f'cleanup - git -C linux checkout {GIT_PULL_BRANCH}; git -C linux branch -D {name}')
    os.system(f'git -C linux checkout {GIT_PULL_BRANCH}')
    os.system(f'git -C linux branch -D {name}')
    print('done')


def mainloop(last_event: Optional[int]) -> int:
    print("Fetching events")
    events = requests.get(PATCHWORK_INSTANCE + 'events/?category=series-completed&project=' + PROJECT)

    if events.status_code != 200:
        print("Events not fetched successfully")
        return False

    print("Got events")
    for event in events.json():
        event_id = int(event['id'])
        if not last_event or event_id > last_event:
            print("Processing", event_id)
            print("Series is", event['payload']['series']['id'])
            apply_series(event['payload']['series'])
            break
    return events.json()[0]['id']


if __name__ == '__main__':
    try:
        with open('last_event', 'r') as f:
            last_event = int(f.read())
    except:
        last_event = None

    while True:
        last_event = mainloop(last_event)
        print("handled events up to", last_event)
        with open('last_event', 'w') as f:
            f.write(str(last_event))
        print("sleeping")
        time.sleep(60)