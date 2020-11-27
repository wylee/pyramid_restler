from runcommands import abort, command, printer
from runcommands.commands import local as _local


@command
def install(update=False):
    if update:
        _local("poetry update")
    _local("poetry install")


@command
def format_code(check=False, where="./"):
    if check:
        printer.hr("Checking code formatting code with black")
        check_arg = "--check"
        raise_on_error = True
    else:
        printer.hr("Formatting code with black")
        check_arg = None
        raise_on_error = False
    result = _local(("black", check_arg, where), raise_on_error=raise_on_error)
    return result


@command
def lint(show_errors=True, where="./", raise_on_error=True):
    printer.hr("Linting code with flake8")
    result = _local(("flake8", where), stdout="capture", raise_on_error=False)
    pieces_of_lint = len(result.stdout_lines)
    if pieces_of_lint:
        ess = "" if pieces_of_lint == 1 else "s"
        message = f"{pieces_of_lint} piece{ess} of lint found"
        if show_errors:
            message = f"{message}:\n{result.stdout.rstrip()}"
            message = (
                f"{message}\nNOTE: Most lint errors can be fixed with `run format-code`"
            )
        if raise_on_error:
            abort(result.return_code, message)
        else:
            printer.error(message)
    else:
        printer.success("No lint found")
    return result


@command
def type_check(incremental=True, raise_on_error=True):
    printer.hr("Type checking with Mypy")
    return _local(
        ("mypy", "--incremental" if incremental else "--no-incremental"),
        raise_on_error=raise_on_error,
    )


@command
def test(*tests, fail_fast=False, where="./tests", check=True):
    printer.hr("Unit testing with `python -m unittest`")
    args = ["python", "-m", "unittest"]
    if fail_fast:
        args.append("-f")
    if tests:
        printer.info("Running specified tests...")
        args.append(tests)
    else:
        printer.info(f"Running tests in {where}...")
        args.extend(("discover", "-t", ".", "-s", where))
    _local(args)

    if not check:
        return

    result = format_code(check=True)
    if result.return_code:
        abort(
            result.return_code,
            "Code needs to be formatted with `run format-code`",
        )

    result = lint(show_errors=False, raise_on_error=False)
    if result.return_code:
        abort(
            result.return_code,
            "Lint needs to be removed (show with `run lint`)",
        )

    result = type_check(incremental=False, raise_on_error=False)
    if result.return_code:
        abort(
            result.return_code,
            "Type errors need to be fixed",
        )


@command
def tox(env=None):
    _local(("tox", ("-e", env) if env else None))
