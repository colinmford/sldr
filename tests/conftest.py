import pytest
from _pytest.terminal import TerminalReporter
import logging
import sys, os
from palaso.sldr.ldml import Ldml

class LdmlFile(object):
    def __init__(self, path, **kw):
        print("Creating ", path)
        for k, v in kw.items():
            setattr(self, k, v)
        self.path = path
        self.ldml = Ldml(self.path)
        self.dirty = False

@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session, exitstatus):
    tr = session.config.pluginmanager.getplugin("terminalreporter")
    if session.config.option.tbstyle == "auto":
        session.config.option.tbstyle = "no"
    yield
    results = {}
    reports = tr.getreports("failed")
    for rep in reports:
        if hasattr(rep, 'location'):
            info = rep.location[2]
            parts = [s.rstrip("]") for s in info.split("[")]
            results.setdefault(parts[0], []).append(os.path.splitext(os.path.basename(parts[1]))[0])
    tr.write_line("")
    for k, r in sorted(results.items()):
        tr.write_line("{}: {}".format(k, ", ".join(r)))


@pytest.fixture(scope="session")
def langid(request):
    return request.param

@pytest.fixture(scope="session")
def ldml(langid):
    ldml = LdmlFile(langid)
    yield ldml
    if ldml.dirty:
        ldml.ldml.save_as(ldml.path, topns=False)

@pytest.fixture(scope="session")
def fixdata(request):
    return request.config.getoption("--fix")

def getallpaths():
    res = {}
    base = os.path.join(os.path.dirname(__file__), '..', 'sldr')
    for l in os.listdir(base):
        if l.endswith('.xml'):
            res[l[:-4].lower()] = os.path.join(base, l)
        elif os.path.isdir(os.path.join(base, l)):
            for t in os.listdir(os.path.join(base, l)):
                if t.endswith('.xml'):
                    res[t[:-4].lower()] = os.path.join(base, l, t)
    return res

def pytest_addoption(parser):
    parser.addoption("-L","--locale", action="append", default=[])
    parser.addoption("-F","--fix", action="store_true", default=[])

def pytest_generate_tests(metafunc):
    if 'langid' not in metafunc.fixturenames:
        return
    vals = [v.lower().replace("-","_") for v in metafunc.config.getoption('locale')]
    allpaths = getallpaths()
    vals = [allpaths[v] for v in vals if v in allpaths]
    if not len(vals):
        vals = sorted(allpaths.values())
    metafunc.parametrize("langid", vals, indirect=True)

def pytest_configure(config):
    # config._inicache["console_output_style"] = "classic"
    config.option.verbose -= 1              # equivalent to one -q, so can be overridden
    #tr = LDMLTerminalReporter(config, sys.stdout)
    #config.pluginmanager.unregister(config.pluginmanager.getplugin("terminalreporter"))
    #config.pluginmanager.register(tr, "terminalreporter")
