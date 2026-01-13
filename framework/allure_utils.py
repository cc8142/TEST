import json
from contextlib import contextmanager

try:
    import allure
    from allure_commons.types import AttachmentType
except Exception:  # pragma: no cover - optional for local runs
    allure = None
    AttachmentType = None


@contextmanager
def step(title):
    if allure:
        with allure.step(title):
            yield
    else:
        yield


def attach_text(name, text):
    if not allure:
        return
    allure.attach(str(text), name=name, attachment_type=AttachmentType.TEXT)


def attach_json(name, payload):
    if not allure:
        return
    try:
        body = json.dumps(payload, ensure_ascii=True, indent=2)
        allure.attach(body, name=name, attachment_type=AttachmentType.JSON)
    except Exception:
        allure.attach(str(payload), name=name, attachment_type=AttachmentType.TEXT)


def attach_file(name, path, mime="text/plain"):
    if not allure:
        return
    if mime == "image/png":
        attachment_type = AttachmentType.PNG
    elif mime == "text/html":
        attachment_type = AttachmentType.HTML
    elif mime == "application/zip":
        attachment_type = AttachmentType.ZIP
    else:
        attachment_type = AttachmentType.TEXT
    allure.attach.file(str(path), name=name, attachment_type=attachment_type)
