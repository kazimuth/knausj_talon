from itertools import chain
from typing import Any, Callable, Dict, Iterator, List, Tuple, TypeVar

from talon import Context, Module, actions, settings

mod = Module()
# rust specific grammar
mod.list("code_type_modifier", desc="List of type modifiers for active language")
mod.list("code_macros", desc="List of macros for active language")
mod.list("code_trait", desc="List of traits for active language")


@mod.action_class
class Actions:
    def code_operator_structure_dereference():
        """Inserts a reference operator"""

    def code_state_implements():
        """Inserts implements block, positioning the cursor appropriately"""

    def code_insert_if_let_some():
        """Inserts if let some block, positioning the cursor appropriately"""

    def code_insert_if_let_error():
        """Inserts if let error block, positioning the cursor appropriately"""

    def code_insert_trait_annotation(type: str):
        """Inserts type annotation for implementor of trait"""

    def code_insert_return_trait(type: str):
        """Inserts a return type for implementor of trait"""

    def code_insert_macro(text: str, selection: str):
        """Inserts a macro and positions the cursor appropriately"""

    def code_insert_macro_array(text: str, selection: str):
        """Inserts a macro array and positions the cursor appropriately"""

    def code_insert_macro_block(text: str, selection: str):
        """Inserts a macro block and positions the cursor appropriately"""

    def code_state_unsafe():
        """Inserts an unsafe block and positions the cursor appropriately"""

    def code_comment_documentation_block():
        """Inserts a block document comment and positions the cursor appropriately"""

    def code_comment_documentation_inner():
        """Inserts an inner document comment and positions the cursor appropriately"""

    def code_comment_documentation_block_inner():
        """Inserts an inner block document comment and positions the cursor appropriately"""


ctx = Context()
ctx.matches = r"""
tag: user.rust
"""

scalar_types = {
    "eye eight": "i8",
    "you eight": "u8",
    "bytes": "u8",
    "eye sixteen": "i16",
    "you sixteen": "u16",
    "eye thirty two": "i32",
    "you thirty two": "u32",
    "eye sixty four": "i64",
    "you sixty four": "u64",
    "eye one hundred and twenty eight": "i128",
    "you one hundred and twenty eight": "u128",
    "eye size": "isize",
    "you size": "usize",
    "float thirty two": "f32",
    "float sixty four": "f64",
    "boolean": "bool",
    "character": "char",
}

compound_types = {
    "unit": "()",
    "array": "[]",
}

standard_library_types = {
    "box": "Box",
    "vector": "Vec",
    "string": "String",
    "string slice": "&str",
    "os string": "OsString",
    "os string slice": "&OsStr",
    "see string": "CString",
    "see string slice": "&CStr",
    "option": "Option",
    "result": "Result",
    "hashmap": "HashMap",
    "hash set": "HashSet",
    "reference count": "Rc",
}

standard_sync_types = {
    "arc": "Arc",
    "barrier": "Barrier",
    "condition variable": "Condvar",
    "mutex": "Mutex",
    "once": "Once",
    "read write lock": "RwLock",
    "receiver": "Receiver",
    "sender": "Sender",
    "sink sender": "SyncSender",
}

FINISH = "FINISH"
TUPLE = "TUPLE"
imaginary_types = {
    "finish": FINISH,
    "tuple": TUPLE,
}

all_types = {
    **scalar_types,
    **compound_types,
    **standard_library_types,
    **standard_sync_types,
    **imaginary_types,
}

standard_function_macros = {
    "panic": "panic!",
    "format": "format!",
    "concatenate": "concat!",
    "print": "print!",
    "print line": "println!",
    "error print line": "eprintln!",
    "to do": "todo!",
}

standard_array_macros = {
    "vector": "vec!",
}

standard_block_macros = {
    "macro rules": "macro_rules!",
}

logging_macros = {
    "debug": "debug!",
    "info": "info!",
    "warning": "warn!",
    "error": "error!",
}

testing_macros = {
    "assert": "assert!",
    "assert equal": "assert_eq!",
    "assert not equal": "assert_ne!",
}

all_function_macros = {
    **standard_function_macros,
    **logging_macros,
    **testing_macros,
}

all_array_macros = {
    **standard_array_macros,
}

all_block_macros = {
    **standard_block_macros,
}

all_macros = {
    **all_function_macros,
    **all_array_macros,
    **all_block_macros,
}

all_function_macro_values = set(all_function_macros.values())
all_array_macro_values = set(all_array_macros.values())
all_block_macro_values = set(all_block_macros.values())

closure_traits = {
    "closure": "Fn",
    "closure once": "FnOnce",
    "closure mutable": "FnMut",
}

conversion_traits = {
    "into": "Into",
    "from": "From",
}

iterator_traits = {
    "iterator": "Iterator",
}

all_traits = {
    **closure_traits,
    **conversion_traits,
    **iterator_traits,
}


# tag: libraries_gui
ctx.lists["user.code_libraries"] = {
    "eye oh": "std::io",
    "file system": "std::fs",
    "envy": "std::env",
    "collections": "std::collections",
}

# tag: functions_common
ctx.lists["user.code_common_function"] = {
    "drop": "drop",
    "catch unwind": "catch_unwind",
    "iterator": "iter",
    "into iterator": "into_iter",
    "from iterator": "from_iter",
    **all_macros,
}

# tag: functions
ctx.lists["user.code_type"] = all_types

# rust specific grammar
ctx.lists["user.code_type_modifier"] = {
    "mutable": "mut ",
    "mute": "mut ",
    "borrowed": "&",
    "borrowed mutable": "&mut ",
    "borrowed mute": "&mut ",
    "mutable borrowed": "&mut ",
    "mute borrowed": "&mut ",
}

# TODO: allow extending this in user configs somehow?
generic_argument_counts: Dict[str, int] = {
    "Box": 1,
    "Vec": 1,
    "Option": 1,
    "Result": 2,
    "HashMap": 2,
    "HashSet": 1,
    "Rc": 1,
    "Arc": 1,
    "Mutex": 1,
    "RwLock": 1,
    "Receiver": 1,
    "Sender": 1,
    "SyncSender": 1,
}


@mod.capture(rule="[{user.code_type_modifier}] {user.code_type}")
def generic_type(m) -> Tuple[str, int, str]:
    """returns (start, arg count, end), negative arg count for n-ary things"""
    m: List[str] = list(m)
    if m[-1] == TUPLE:
        result = ("(", -1, ")")
    elif m[-1] in generic_argument_counts:
        result = ("".join(m + ["<"]), generic_argument_counts[m[-1]], ">")
    else:
        result = ("".join(m), 0, "")
    return result


@ctx.capture("user.code_type", rule="<user.generic_type>+")
def code_type(m) -> str:
    """Parses a type, inserting brackets for generic arguments.
    This knows about standard library generic types and how many arguments they take.

    To start a tuple type, say "tuple"; to end a tuple type, say "finish".
    If you don't end a tuple type, it'll automatically be closed.

    For example:
    'vector' -> 'Vec<>'
    'vector eye thirty two' -> 'Vec<i32>'
    'hash map borrowed mute eye thirty two string' -> 'HashMap<&mut i32, String>'
    'borrowed mute hash map eye thirty two string' -> '&mut HashMap<i32, String>'
    'tuple eye thirty two character string' -> '(i32, char, String)'
    'hash map tuple boolean boolean finish string' -> 'HashMap<(boolean, boolean), String)'
    """

    def parse(tokens: Iterator[Tuple[str, int, str]]) -> Iterator[str]:
        """Consume some number of tokens, yielding a sequence of strs That can be joined with '' to give a single type."""
        try:
            start, expected_args, end = next(tokens)
        except StopIteration:
            # this seems silly but is mandated by PEP 479
            return

        if start == FINISH:
            # we haven't started a tuple, and this isn't a real type, so suppress it
            return

        if expected_args == 0:
            # simplest case, a non-generic type
            yield start

        elif expected_args > 0:
            # we expect some concrete number of arguments
            yield start
            for i in range(expected_args):
                # each yield from corresponds to a single type
                try:
                    yield from parse(tokens)
                except StopIteration:
                    return

                if i < expected_args - 1:
                    yield ", "
            yield end
        else:
            # expected_args < 0, ie an n-ary object like a tuple
            yield start
            written = 0
            while True:
                # peek
                try:
                    next_start, next_expected, next_end = next(tokens)
                    stopping = next_start == FINISH
                except StopIteration:
                    # stream has ended, but we're inside an n-ary:
                    # optimistically close it.
                    stopping = True

                if stopping:
                    if written == 1:
                        # (T, ) != (T), so we can't get rid of the comma in this case
                        yield ", "
                    break
                # we're not done, but we might need a comma
                elif written > 0:
                    yield ", "

                # reconstruct the iterator and do this step
                yield from parse(chain([(next_start, next_expected, next_end)], tokens))
                written += 1
            yield end

    return "".join(parse(iter(m)))


def code_type_(*args):
    return code_type([generic_type(arg) for arg in args])


assert code_type_(["Vec"]) == "Vec<>"
assert code_type_(["Vec"], ["i32"]) == "Vec<i32>"
assert (
    code_type_(["HashMap"], ["&mut ", "i32"], ["String"]) == "HashMap<&mut i32, String>"
)
assert code_type_(["HashMap"], ["&mut ", "i32"]) == "HashMap<&mut i32, >"
assert (
    code_type_(["&mut ", "HashMap"], ["i32"], ["String"]) == "&mut HashMap<i32, String>"
)
assert (
    code_type_(["HashMap"], ["Vec"], ["i32"], ["HashMap"], ["String"], ["()"])
    == "HashMap<Vec<i32>, HashMap<String, ()>>"
)
assert (
    code_type_(["HashMap"], [TUPLE], ["bool"], ["bool"], [FINISH], ["String"])
    == "HashMap<(bool, bool), String>"
)
assert code_type_([TUPLE], ["i32"], ["i32"], ["i32"]) == "(i32, i32, i32)"
assert code_type_([TUPLE], ["i32"]) == "(i32, )"
assert (
    code_type_([TUPLE], [TUPLE], ["i32"], ["i32"], [FINISH], ["String"])
    == "((i32, i32), String)"
)
assert code_type_([TUPLE], [FINISH]) == "()"


ctx.lists["user.code_macros"] = all_macros

ctx.lists["user.code_trait"] = all_traits


@ctx.action_class("user")
class UserActions:

    # tag: comment_line

    def code_comment_line_prefix():
        actions.auto_insert("// ")

    # tag: comment_documentation

    def code_comment_documentation():
        actions.auto_insert("/// ")

    # tag: imperative

    def code_block():
        actions.auto_insert("{}")
        actions.edit.left()
        actions.key("enter")

    def code_state_if():
        actions.auto_insert("if ")

    def code_state_else_if():
        actions.auto_insert(" else if ")

    def code_state_else():
        actions.user.insert_between(" else { ", " }")

    def code_state_switch():
        actions.auto_insert("match ")

    def code_state_for():
        actions.auto_insert("for  in  {}")
        actions.edit.left()
        actions.key("enter")
        actions.edit.up()
        actions.edit.line_end()
        repeat_call(6, actions.edit.left)

    def code_state_while():
        actions.auto_insert("while  {}")
        actions.edit.left()
        actions.key("enter")
        actions.edit.up()
        actions.edit.line_end()
        repeat_call(2, actions.edit.left)

    def code_state_infinite_loop():
        actions.user.insert_between("loop {", "}")
        actions.key("enter")

    def code_state_return():
        actions.auto_insert("return ")

    def code_break():
        actions.auto_insert("break;")

    def code_next():
        actions.auto_insert("continue;")

    # tag: object_oriented

    def code_operator_object_accessor():
        actions.auto_insert(".")

    def code_self():
        actions.auto_insert("self")

    def code_define_class():
        actions.auto_insert("struct ")

    # tag: data_bool

    def code_insert_true():
        actions.auto_insert("true")

    def code_insert_false():
        actions.auto_insert("false")

    # tag: data_null

    def code_insert_null():
        actions.auto_insert("None")

    def code_insert_is_null():
        actions.auto_insert(".is_none()")

    def code_insert_is_not_null():
        actions.auto_insert(".is_some()")

    # tag: functions

    def code_default_function(text: str):
        actions.user.code_private_function(text)

    def code_private_function(text: str):
        actions.auto_insert("fn ")
        formatter = settings.get("user.code_private_function_formatter")
        function_name = actions.user.formatted_text(text, formatter)
        actions.user.code_insert_function(function_name, None)

    def code_protected_function(text: str):
        actions.auto_insert("pub(crate) fn ")
        formatter = settings.get("user.code_protected_function_formatter")
        function_name = actions.user.formatted_text(text, formatter)
        actions.user.code_insert_function(function_name, None)

    def code_public_function(text: str):
        actions.auto_insert("pub fn ")
        formatter = settings.get("user.code_public_function_formatter")
        function_name = actions.user.formatted_text(text, formatter)
        actions.user.code_insert_function(function_name, None)

    def code_insert_type_annotation(type: str):
        actions.auto_insert(f": {type}")

    def code_insert_return_type(type: str):
        actions.auto_insert(f" -> {type}")

    # tag: functions_gui

    def code_insert_function(text: str, selection: str):
        code_insert_function_or_macro(text, selection, "(", ")")

    # tag: libraries

    def code_import():
        actions.auto_insert("use ")

    # tag: libraries_gui

    def code_insert_library(text: str, selection: str):
        actions.user.paste(f"use {selection}")

    # tag: operators_array

    def code_operator_subscript():
        actions.auto_insert("[]")
        actions.edit.left()

    # tag: code_operators_assignment

    def code_operator_assignment():
        actions.auto_insert(" = ")

    def code_operator_subtraction_assignment():
        actions.auto_insert(" -= ")

    def code_operator_addition_assignment():
        actions.auto_insert(" += ")

    def code_operator_multiplication_assignment():
        actions.auto_insert(" *= ")

    def code_operator_division_assignment():
        actions.auto_insert(" /= ")

    def code_operator_modulo_assignment():
        actions.auto_insert(" %= ")

    def code_operator_bitwise_and_assignment():
        actions.auto_insert(" &= ")

    def code_operator_bitwise_or_assignment():
        actions.auto_insert(" |= ")

    def code_operator_bitwise_exclusive_or_assignment():
        actions.auto_insert(" ^= ")

    def code_operator_bitwise_left_shift_assignment():
        actions.auto_insert(" <<= ")

    def code_operator_bitwise_right_shift_assignment():
        actions.auto_insert(" >>= ")

    # tag: operators_bitwise

    def code_operator_bitwise_and():
        actions.auto_insert(" & ")

    def code_operator_bitwise_or():
        actions.auto_insert(" | ")

    def code_operator_bitwise_exclusive_or():
        actions.auto_insert(" ^ ")

    def code_operator_bitwise_left_shift():
        actions.auto_insert(" << ")

    def code_operator_bitwise_right_shift():
        actions.auto_insert(" >> ")

    # tag: operators_math

    def code_operator_subtraction():
        actions.auto_insert(" - ")

    def code_operator_addition():
        actions.auto_insert(" + ")

    def code_operator_multiplication():
        actions.auto_insert(" * ")

    def code_operator_exponent():
        actions.auto_insert(".pow()")
        actions.edit.left()

    def code_operator_division():
        actions.auto_insert(" / ")

    def code_operator_modulo():
        actions.auto_insert(" % ")

    def code_operator_equal():
        actions.auto_insert(" == ")

    def code_operator_not_equal():
        actions.auto_insert(" != ")

    def code_operator_greater_than():
        actions.auto_insert(" > ")

    def code_operator_greater_than_or_equal_to():
        actions.auto_insert(" >= ")

    def code_operator_less_than():
        actions.auto_insert(" < ")

    def code_operator_less_than_or_equal_to():
        actions.auto_insert(" <= ")

    def code_operator_and():
        actions.auto_insert(" && ")

    def code_operator_or():
        actions.auto_insert(" || ")

    def code_operator_increment():
        actions.auto_insert(" += 1")

    # rust specific grammar

    def code_operator_structure_dereference():
        actions.auto_insert("*")

    def code_insert_if_let_some():
        actions.user.insert_between("if let Some(", ")")

    def code_insert_if_let_okay():
        actions.user.insert_between("if let Ok(", ")")

    def code_insert_if_let_error():
        actions.user.insert_between("if let Err(", ")")

    def code_state_implements():
        actions.auto_insert("impl  {}")
        actions.edit.left()
        actions.key("enter")
        actions.edit.up()
        actions.edit.line_end()
        repeat_call(2, actions.edit.left)

    def code_insert_trait_annotation(type: str):
        actions.auto_insert(f": impl {type}")

    def code_insert_return_trait(type: str):
        actions.auto_insert(f" -> impl {type}")

    def code_insert_macro(text: str, selection: str):
        if text in all_array_macro_values:
            code_insert_function_or_macro(text, selection, "[", "]")
        elif text in all_block_macro_values:
            code_insert_function_or_macro(text, selection, "{", "}")
        else:
            code_insert_function_or_macro(text, selection, "(", ")")

    def code_state_unsafe():
        actions.user.insert_between("unsafe {", "}")
        actions.key("enter")

    def code_comment_documentation_block():
        actions.user.insert_between("/**", "*/")
        actions.key("enter")

    def code_comment_documentation_inner():
        actions.auto_insert("//! ")

    def code_comment_documentation_block_inner():
        actions.user.insert_between("/*!", "*/")
        actions.key("enter")


def code_insert_function_or_macro(
    text: str,
    selection: str,
    left_delim: str,
    right_delim: str,
):
    if selection:
        out_text = text + f"{left_delim}{selection}{right_delim}"
    else:
        out_text = text + f"{left_delim}{right_delim}"
    actions.user.paste(out_text)
    actions.edit.left()


RT = TypeVar("RT")  # return type


def repeat_call(n: int, f: Callable[..., RT], *args: Any, **kwargs: Any):
    for i in range(n):
        f(*args, **kwargs)
