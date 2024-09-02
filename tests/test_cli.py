import argparse
import collections
import hashlib
import os
import pathlib
import subprocess
import sys


def hash_file(path):
    """
    Returns the hash of a file.
    Based on https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
    """

    # Return error as hash, if file does not exist
    if not os.path.exists(path):
        return f"error hashing file, file does not exist: {path}"

    # BUF_SIZE is totally arbitrary, change for your app!
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

    # Use sha1
    sha1 = hashlib.sha1()

    # Read and hash file (with buffering)
    with open(path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)

    # Return hash
    return sha1.hexdigest()


# Test CLI
def test_main():
    # Check for update argument
    parser = argparse.ArgumentParser(description="brickmos golden file tests")
    parser.add_argument(
        "--update",
        dest="update",
        action="store_true",
        default=False,
        help="updates the golden files",
    )
    args = parser.parse_args()

    # Prepare paths
    base_dir = pathlib.Path(__file__).parent.joinpath("..").resolve(strict=True)
    script_path = str(base_dir.joinpath("run.py").resolve(strict=True))
    output_dir = str(base_dir.joinpath("tests/output").resolve())
    data_dir = str(base_dir.joinpath("tests/testdata").resolve(strict=True))

    # Prepare
    os.chdir(base_dir)
    os.makedirs(output_dir, exist_ok=True)
    for f in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, f))
    base_args = [sys.executable, script_path]
    CliTest = collections.namedtuple(
        "Test",
        [
            "args",
            "golden_log",
            "golden_pixelated",
            "golden_output",
            "golden_bricklink",
        ],
    )

    # Define test cases
    tests = [
        CliTest(
            [
                "-i",
                os.path.join(data_dir, "iron-man.jpg"),
                "--spares",
                "5",
                "--size",
                "64x64",
                "--grid_cell",
                "4x4",
            ],
            os.path.join(data_dir, "iron-man.jpg.golden.log"),
            os.path.join(data_dir, "iron-man.jpg.golden.pixelated.hash"),
            os.path.join(data_dir, "iron-man.jpg.golden.output.hash"),
            os.path.join(data_dir, "iron-man.jpg.golden.bricklink.xml"),
        ),
    ]

    # Run all test cases
    for test in tests:
        # Assemble command and arguments
        cmd = [*base_args, *test.args]
        cmd.extend(
            [
                "-o",
                output_dir,
                "--no_preview",
            ]
        )

        # Log
        cmd_string = " ".join(test.args)
        print(f"Invoking: {cmd_string}")

        # Run command
        result = subprocess.run(cmd, stdout=subprocess.PIPE)

        # Expect no errors
        assert result.returncode == 0

        # Compare log output
        output = result.stdout.decode("utf-8")
        if args.update:
            with open(test.golden_log, "w") as file:
                file.write(output)
        else:
            expected = ""
            with open(test.golden_log) as file:
                expected = file.read()
            assert output == expected, f"Expected:\n{expected}\nGot:\n{output}"

        # Compare hash of pixelated file
        pix_hash = hash_file(os.path.join(output_dir, "2.pixelated.jpg"))
        if args.update:
            with open(test.golden_pixelated, "w") as file:
                file.write(pix_hash)
        else:
            expected = ""
            with open(test.golden_pixelated) as file:
                expected = file.read()
            assert pix_hash == expected, f"Expected: {expected}, Got: {pix_hash}"

        # Compare hash of output file
        out_hash = hash_file(os.path.join(output_dir, "3.output.jpg"))
        if args.update:
            with open(test.golden_output, "w") as file:
                file.write(out_hash)
        else:
            expected = ""
            with open(test.golden_output) as file:
                expected = file.read()
            assert out_hash == expected, f"Expected: {expected}, Got: {out_hash}"

        # Compare bricklink export
        bricklink = ""
        with open(os.path.join(output_dir, "bricklink.xml")) as f:
            bricklink = f.read()
        if args.update:
            with open(test.golden_bricklink, "w") as file:
                file.write(bricklink)
        else:
            expected = ""
            with open(test.golden_bricklink) as file:
                expected = file.read()
            assert bricklink == expected, f"Expected:\n{expected}\nGot:\n{bricklink}"


if __name__ == "__main__":
    test_main()
    print("Everything passed")
