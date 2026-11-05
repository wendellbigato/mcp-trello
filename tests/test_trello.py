"""Testes do cliente, dos modelos e da importação sem credenciais."""

import os
import subprocess
import sys
import tempfile
import unittest

import httpx

from mcp_trello.client import TrelloAPIError, TrelloClient
from mcp_trello.types import TrelloCommentData, TrelloCredentials, TrelloLabel

_CARD_ID = "a" * 24
_LIST_ID = "b" * 24


class TypesTest(unittest.TestCase):
    def test_label_aceita_cor_nula(self):
        label = TrelloLabel.model_validate(
            {"id": "abc12345", "name": None, "color": None, "uses": 3}
        )
        self.assertIsNone(label.color)
        self.assertIsNone(label.name)

    def test_comentario_tipa_o_card_embutido(self):
        comment = TrelloCommentData.model_validate(
            {
                "text": "feito",
                "card": {"id": "a" * 24, "name": "Card", "idShort": 4, "extra": True},
                "board": {"id": "b" * 24, "name": "Board"},
            }
        )
        self.assertIsNotNone(comment.card)
        assert comment.card is not None
        self.assertEqual(comment.card.name, "Card")
        self.assertEqual(comment.card.idShort, 4)
        self.assertIsNone(comment.list)


class ClientErrorTest(unittest.TestCase):
    def test_404_nao_revela_credenciais(self):
        secret_key = "key-secreta-de-teste"
        secret_token = "token-secreto-de-teste"

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertIn("key=", str(request.url))
            return httpx.Response(404)

        client = TrelloClient(
            TrelloCredentials(api_key=secret_key, token=secret_token)
        )
        client._http.close()
        client._http = httpx.Client(
            base_url="https://api.trello.com/1",
            params={"key": secret_key, "token": secret_token},
            transport=httpx.MockTransport(handler),
        )
        try:
            with self.assertRaises(TrelloAPIError) as caught:
                client.get_board("a" * 24)
        finally:
            client.close()

        message = str(caught.exception)
        self.assertEqual(caught.exception.status_code, 404)
        self.assertEqual(caught.exception.path, f"/boards/{'a' * 24}")
        self.assertNotIn("key=", message)
        self.assertNotIn("token=", message)
        self.assertNotIn(secret_key, message)
        self.assertNotIn(secret_token, message)
        self.assertIsNone(caught.exception.__cause__)

    def test_lista_quadros_abertos(self):
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["path"] = request.url.path
            seen["filter"] = request.url.params["filter"]
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "a" * 24,
                        "name": "Escola",
                        "desc": None,
                        "url": "https://trello.com/b/abc/escola",
                        "closed": False,
                        "extra": True,
                    }
                ],
            )

        client = TrelloClient(TrelloCredentials(api_key="key", token="token"))
        client._http.close()
        client._http = httpx.Client(
            base_url="https://api.trello.com/1",
            transport=httpx.MockTransport(handler),
        )
        try:
            boards = client.list_boards()
        finally:
            client.close()

        self.assertEqual(seen["path"], "/1/members/me/boards")
        self.assertEqual(seen["filter"], "open")
        self.assertEqual(boards[0].name, "Escola")
        self.assertIsNone(boards[0].desc)
        self.assertFalse(boards[0].closed)

    def test_lista_quadros_inclui_fechados(self):
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["filter"] = request.url.params["filter"]
            return httpx.Response(200, json=[])

        client = TrelloClient(TrelloCredentials(api_key="key", token="token"))
        client._http.close()
        client._http = httpx.Client(
            base_url="https://api.trello.com/1",
            transport=httpx.MockTransport(handler),
        )
        try:
            self.assertEqual(client.list_boards(include_closed=True), [])
        finally:
            client.close()

        self.assertEqual(seen["filter"], "all")

    def test_id_invalido_nao_monta_url(self):
        client = TrelloClient(TrelloCredentials(api_key="key", token="token"))
        try:
            with self.assertRaises(ValueError):
                client.get_board("../members/me?token=vazou")
        finally:
            client.close()

    def test_mover_card_nao_revela_credenciais(self):
        secret_key = "key-secreta-de-teste"
        secret_token = "token-secreto-de-teste"
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["method"] = request.method
            seen["path"] = request.url.path
            self.assertIn(f"idList={_LIST_ID}", str(request.url))
            return httpx.Response(
                401,
                json={"message": "unauthorized"},
            )

        client = TrelloClient(
            TrelloCredentials(api_key=secret_key, token=secret_token)
        )
        client._http.close()
        client._http = httpx.Client(
            base_url="https://api.trello.com/1",
            params={"key": secret_key, "token": secret_token},
            transport=httpx.MockTransport(handler),
        )
        try:
            with self.assertRaises(TrelloAPIError) as caught:
                client.move_card(_CARD_ID, _LIST_ID, pos="top")
        finally:
            client.close()

        message = str(caught.exception)
        self.assertEqual(seen["method"], "PUT")
        self.assertEqual(seen["path"], f"/1/cards/{_CARD_ID}")
        self.assertEqual(caught.exception.path, f"/cards/{_CARD_ID}")
        self.assertNotIn("key=", message)
        self.assertNotIn("token=", message)
        self.assertNotIn(secret_key, message)
        self.assertNotIn(secret_token, message)

    def test_update_sem_texto_nao_chama_a_api(self):
        client = TrelloClient(TrelloCredentials(api_key="key", token="token"))
        try:
            with self.assertRaises(ValueError):
                client.update_card(_CARD_ID)
        finally:
            client.close()

    def test_comentario_vazio_nao_chama_a_api(self):
        client = TrelloClient(TrelloCredentials(api_key="key", token="token"))
        try:
            with self.assertRaises(ValueError):
                client.add_card_comment(_CARD_ID, "   ")
        finally:
            client.close()


class ImportTest(unittest.TestCase):
    def test_importar_sem_credenciais_nao_encerra_o_processo(self):
        env = os.environ.copy()
        env.pop("TRELLO_API_KEY", None)
        env.pop("TRELLO_TOKEN", None)
        with tempfile.TemporaryDirectory() as empty:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import mcp_trello.server; print('importou')",
                ],
                cwd=empty,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("importou", completed.stdout)
        self.assertNotIn("SystemExit", completed.stderr)

    def test_primeiro_uso_avisa_credencial_ausente(self):
        env = os.environ.copy()
        env.pop("TRELLO_API_KEY", None)
        env.pop("TRELLO_TOKEN", None)
        with tempfile.TemporaryDirectory() as empty:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from mcp_trello.server import get_client\n"
                    "try:\n"
                    "    get_client()\n"
                    "except RuntimeError:\n"
                    "    pass\n",
                ],
                cwd=empty,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("TRELLO_API_KEY e TRELLO_TOKEN são obrigatórios", completed.stderr)
