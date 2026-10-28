"""Executable state model for an educational simulation; not a CMS or security test."""
from dataclasses import dataclass

ERROR = "Не вдалося увійти"

@dataclass
class Model:
    authenticated: bool = False
    screen: str = "A"

    def open_editor(self):
        self.screen = "C" if self.authenticated else "B"
        return self.screen

    def login(self, account, password, active=True):
        self.authenticated = account == "EDITOR-A" and password == "PASSWORD-OK" and active
        self.screen = "C" if self.authenticated else "E"
        return self.screen, "" if self.authenticated else ERROR

    def direct_request(self):
        return (200, "EDITOR") if self.authenticated else (403, "")

    def logout(self):
        self.authenticated, self.screen = False, "A"


def run():
    results = []
    m = Model()
    assert m.open_editor() == "B"
    assert m.login("EDITOR-A", "PASSWORD-OK")[0] == "C"
    assert m.direct_request() == (200, "EDITOR")
    results.append("T1 PASS: A -> B -> C; authorized model request=200")
    m = Model(); m.open_editor()
    wrong = m.login("EDITOR-A", "PASSWORD-WRONG")
    assert wrong == ("E", ERROR) and m.direct_request() == (403, "")
    results.append("T2 PASS: B -> E; no protected model content")
    m = Model(); m.open_editor()
    unknown = m.login("UNKNOWN", "PASSWORD-OK")
    assert unknown == wrong
    results.append("T3 PASS: unknown account and wrong password have identical output")
    m = Model()
    assert m.direct_request() == (403, "")
    results.append("T4 PASS: unauthenticated direct request=403; empty content")
    m.login("EDITOR-A", "PASSWORD-OK"); m.logout()
    assert m.screen == "A" and m.direct_request() == (403, "")
    assert m.open_editor() == "B"
    results.append("T5 PASS: C -> A -> B; direct request after logout=403")
    m = Model()
    assert m.login("EDITOR-A", "PASSWORD-OK", active=False) == ("E", ERROR)
    assert m.direct_request() == (403, "")
    results.append("T6 PASS: inactive account cannot authorize")
    m = Model(); m.login("UNKNOWN", "PASSWORD-OK")
    assert m.open_editor() == "B"
    assert m.login("EDITOR-A", "PASSWORD-OK")[0] == "C"
    results.append("T7 PASS: E -> B -> C on retry with valid model data")
    return results

if __name__ == "__main__":
    print("S-01 EDUCATIONAL MODEL ONLY")
    print("\n".join(run()))
