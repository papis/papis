import re
import os
import glob

import json
import tempfile

import yaml

import papis.yaml
import papis.bibtex
import papis.config
import papis.document
from papis.commands.export import run, cli

import tests
import tests.cli


Loader = papis.yaml.YAML_LOADER


class TestRun(tests.cli.TestWithLibrary):

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_bibtex(self) -> None:
        docs = self.get_docs()
        string = run(docs, to_format="bibtex")
        self.assertTrue(string)
        data = papis.bibtex.bibtex_to_dict(string)
        self.assertTrue(data)

    def test_json(self) -> None:
        docs = self.get_docs()
        string = run(docs, to_format="json")
        self.assertTrue(string)
        data = json.loads(string)
        self.assertTrue(data)

    def test_yaml(self) -> None:
        docs = self.get_docs()
        string = run(docs, to_format="yaml")
        self.assertTrue(string)

        with tempfile.NamedTemporaryFile("w+", delete=False) as fd:
            path = fd.name
            fd.write(string)

        with open(path, "r") as fd:
            data = list(yaml.load_all(fd, Loader=Loader))

        self.assertIsNot(data, None)
        self.assertTrue(data)
        os.unlink(path)


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_main(self) -> None:
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_json(self) -> None:
        result = self.invoke([
            "krishnamurti", "--format", "json"
        ])
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.stdout_bytes.decode())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertIsNot(re.match(r".*Krishnamurti.*", data[0]["author"]), None)

        # output stdout
        with tempfile.NamedTemporaryFile(delete=False) as f:
            outfile = f.name

        result = self.invoke([
            "Krishnamurti", "--format", "json", "--out", outfile
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(outfile))

        with open(outfile) as fd:
            data = json.load(fd)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertIsNot(re.match(r".*Krishnamurti.*", data[0]["author"]), None)
        os.unlink(outfile)

    def test_yaml(self) -> None:
        result = self.invoke([
            "krishnamurti", "--format", "yaml"
        ])
        self.assertEqual(result.exit_code, 0)
        data = yaml.safe_load(result.stdout_bytes)
        assert re.match(r".*Krishnamurti.*", data["author"]) is not None

        with tempfile.NamedTemporaryFile(delete=False) as f:
            outfile = f.name

        result = self.invoke([
            "Krishnamurti", "--format", "yaml", "--out", outfile
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(outfile))

        with open(outfile) as fd:
            data = yaml.safe_load(fd.read())

        self.assertIsNot(data, None)
        self.assertIsNot(re.match(r".*Krishnamurti.*", data["author"]), None)
        os.unlink(outfile)

    def test_folder(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            outdir = os.path.join(d, "export")

            result = self.invoke(["krishnamurti", "--folder", "--out", outdir])
            self.assertTrue(os.path.exists(outdir))
            self.assertTrue(os.path.isdir(outdir))
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout_bytes, b"")

            doc = papis.document.from_folder(outdir)
            self.assertIsNot(doc, None)
            self.assertIsNot(re.match(r".*Krishnamurti.*", doc["author"]), None)

    def test_folder_all(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            outdir = os.path.join(d, "export")

            result = self.invoke(["--all", "--folder", "--out", outdir])
            self.assertTrue(os.path.exists(outdir))
            self.assertTrue(os.path.isdir(outdir))
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout_bytes, b"")

            dirs = glob.glob(os.path.join(outdir, "*"))
            self.assertGreater(len(dirs), 1)
            for d in dirs:
                self.assertTrue(os.path.exists(d))
                self.assertTrue(os.path.isdir(d))

    def test_no_documents(self) -> None:
        result = self.invoke(["-f", "bibtex", "__no_document__"])
        self.assertEqual(result.exit_code, 0)
