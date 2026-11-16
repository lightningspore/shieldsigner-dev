# SPDX-License-Identifier: MIT
# Actual frozen original navigation classes; these local Views are test fixtures.
from seedsigner_port.navigation import Destination, BackStack


class View:
    has_redirect = False

    def __init__(self, number=9):
        self.number = number

    def run(self):
        return self.number + 1


class Redirect(View):
    has_redirect = True

    def get_redirect(self):
        return 'redirect-result'


a = Destination(View)
assert a == Destination(View, {})
assert a.run() == 10 and a.view_args == {}
assert a == Destination(View, {}, True, True)
assert Destination(View, {'number': 41}).run() == 42
assert Destination(Redirect, {'number': 41}).run() == 'redirect-result'
secret = {
    'passphrase': 'navigation-test-secret',
    'items': [{'PIN': 'navigation-test-pin', 'public': 'visible'}],
}
text = repr(Destination(View, secret, clear_history=True))
assert 'navigation-test-secret' not in text and 'navigation-test-pin' not in text
assert 'visible' in text and 'redacted' in text
history = BackStack([a, Destination(Redirect)])
assert len(history) == 2 and 'Redirect' in repr(history)
assert history.pop().View_cls == Redirect
print('@@PASS original-navigation-frozen')
