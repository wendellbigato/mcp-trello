"""Testes do cliente, dos modelos e da importação sem credenciais."""

import asyncio
import os
import subprocess
import sys
import tempfile
import unittest

import httpx

from mcp_trello.client import TrelloAPIError, TrelloClient
from mcp_trello.types import TrelloCommentData, TrelloCredentials, TrelloLabel


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

        async def call() -> None:
            client = TrelloClient(
                TrelloCredentials(api_key=secret_key, token=secret_token)
            )
            await client._http.aclose()
            client._http = httpx.AsyncClient(
                base_url="https://api.trello.com/1",
                params={"key": secret_key, "token": secret_token},
                transport=httpx.MockTransport(handler),
            )
            try:
                await client.get_board("a" * 24)
            finally:
                await client.aclose()

        with self.assertRaises(TrelloAPIError) as caught:
            asyncio.run(call())

        message = str(caught.exception)
        self.assertEqual(caught.exception.status_code, 404)
        self.assertEqual(caught.exception.path, f"/boards/{'a' * 24}")
        self.assertNotIn("key=", message)
        self.assertNotIn("token=", message)
        self.assertNotIn(secret_key, message)
        self.assertNotIn(secret_token, message)
        self.assertIsNone(caught.exception.__cause__)

    def test_id_invalido_nao_monta_url(self):
        async def call() -> None:
            client = TrelloClient(TrelloCredentials(api_key="key", token="token"))
            try:
                await client.get_board("../members/me?token=vazou")
            finally:
                await client.aclose()

        with self.assertRaises(ValueError):
            asyncio.run(call())


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
