#!/bin/sh

set -e

usage() {
    printf '%s\n' "Usage: $0 --agent codex|claude|both [--source-dir PATH --revision LABEL]"
}

die() {
    printf 'xfetch installer: %s\n' "$1" >&2
    exit 1
}

XFETCH_MARKER_NAME=.xfetch-managed
XFETCH_MARKER_VALUE=xfetch-installer-managed-v1
XFETCH_REPOSITORY=https://github.com/guchengwei/xfetch
XFETCH_COMMIT_URL=https://api.github.com/repos/guchengwei/xfetch/commits/main
XFETCH_UV_URL=https://astral.sh/uv/install.sh

xfetch_path_exists() {
    [ -e "$1" ] || [ -L "$1" ] || [ -h "$1" ]
}

xfetch_is_symlink() {
    [ -L "$1" ] || [ -h "$1" ]
}

xfetch_directory_has_entries() {
    XFETCH_CANDIDATE=
    for XFETCH_CANDIDATE in "$1"/* "$1"/.[!.]* "$1"/..?*; do
        if xfetch_path_exists "$XFETCH_CANDIDATE"; then
            return 0
        fi
    done
    return 1
}

xfetch_preflight_directory() {
    XFETCH_DIRECTORY=$1
    if xfetch_path_exists "$XFETCH_DIRECTORY"; then
        [ -d "$XFETCH_DIRECTORY" ] || die "destination is not a directory: $XFETCH_DIRECTORY"
        xfetch_is_symlink "$XFETCH_DIRECTORY" && die "destination is a symlink: $XFETCH_DIRECTORY"
        XFETCH_MARKER=$XFETCH_DIRECTORY/$XFETCH_MARKER_NAME
        if xfetch_path_exists "$XFETCH_MARKER"; then
            [ -f "$XFETCH_MARKER" ] || die "managed marker is not a file: $XFETCH_MARKER"
            xfetch_is_symlink "$XFETCH_MARKER" && die "managed marker is a symlink: $XFETCH_MARKER"
            XFETCH_MARKER_LINE=$(sed -n '1p' "$XFETCH_MARKER")
            [ "$XFETCH_MARKER_LINE" = "$XFETCH_MARKER_VALUE" ] ||
                die "destination has a different managed marker: $XFETCH_DIRECTORY"
        elif xfetch_directory_has_entries "$XFETCH_DIRECTORY"; then
            die "refusing to overwrite an unowned destination: $XFETCH_DIRECTORY"
        fi
    fi
}

agent=
source_dir=
source_dir_set=0
revision=
revision_set=0

while [ "$#" -gt 0 ]; do
    case $1 in
        --agent)
            [ "$#" -ge 2 ] || die "--agent requires a value"
            agent=$2
            shift 2
            ;;
        --agent=*)
            agent=$(printf '%s\n' "$1" | sed 's/^--agent=//')
            shift
            ;;
        --source-dir)
            [ "$#" -ge 2 ] || die "--source-dir requires a path"
            source_dir=$2
            source_dir_set=1
            shift 2
            ;;
        --source-dir=*)
            source_dir=$(printf '%s\n' "$1" | sed 's/^--source-dir=//')
            source_dir_set=1
            shift
            ;;
        --revision)
            [ "$#" -ge 2 ] || die "--revision requires a label"
            revision=$2
            revision_set=1
            shift 2
            ;;
        --revision=*)
            revision=$(printf '%s\n' "$1" | sed 's/^--revision=//')
            revision_set=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            die "unknown argument: $1"
            ;;
    esac
done

[ -n "$agent" ] || { usage >&2; die "--agent is required"; }
case $agent in
    codex|claude|both) ;;
    *) die "--agent must be codex, claude, or both" ;;
esac

if [ "$source_dir_set" -ne "$revision_set" ]; then
    die "--source-dir and --revision must be provided together"
fi
if [ "$source_dir_set" -eq 1 ] && [ -z "$source_dir" ]; then
    die "--source-dir requires a path"
fi
if [ "$revision_set" -eq 1 ] && [ -z "$revision" ]; then
    die "--revision requires a label"
fi

if [ -n "$HOME" ]; then
    XFETCH_HOME_DIR=$(cd "$HOME" 2>/dev/null && pwd -P) ||
        die "HOME does not name a directory: $HOME"
else
    die 'HOME is not set'
fi

XFETCH_RUNTIME_ROOT=$XFETCH_HOME_DIR/.local/share/xfetch
XFETCH_CODEX_SKILL=$XFETCH_HOME_DIR/.agents/skills/xfetch
XFETCH_CLAUDE_SKILL=$XFETCH_HOME_DIR/.claude/skills/xfetch

xfetch_preflight_directory "$XFETCH_RUNTIME_ROOT"
case $agent in
    codex) xfetch_preflight_directory "$XFETCH_CODEX_SKILL" ;;
    claude) xfetch_preflight_directory "$XFETCH_CLAUDE_SKILL" ;;
    both)
        xfetch_preflight_directory "$XFETCH_CODEX_SKILL"
        xfetch_preflight_directory "$XFETCH_CLAUDE_SKILL"
        ;;
esac

XFETCH_TMP_BASE=/tmp
if [ -n "$TMPDIR" ]; then
    XFETCH_TMP_BASE=$TMPDIR
fi
XFETCH_TMP_DIR=$(mktemp -d "$XFETCH_TMP_BASE/xfetch-install.XXXXXX") ||
    die 'could not create a temporary directory'
trap 'rm -rf "$XFETCH_TMP_DIR"' EXIT HUP INT TERM

XFETCH_CURL_BIN=$(command -v curl 2>/dev/null || true)
XFETCH_WGET_BIN=$(command -v wget 2>/dev/null || true)

xfetch_fetch() {
    XFETCH_URL=$1
    XFETCH_DESTINATION=$2
    if [ -n "$XFETCH_CURL_BIN" ]; then
        "$XFETCH_CURL_BIN" -fsSL "$XFETCH_URL" -o "$XFETCH_DESTINATION"
    elif [ -n "$XFETCH_WGET_BIN" ]; then
        "$XFETCH_WGET_BIN" -qO "$XFETCH_DESTINATION" "$XFETCH_URL"
    else
        die 'curl or wget is required for downloads'
    fi
}

if [ "$source_dir_set" -eq 1 ]; then
    XFETCH_SOURCE_ROOT=$(cd "$source_dir" 2>/dev/null && pwd -P) ||
        die "source directory does not exist: $source_dir"
    [ -f "$XFETCH_SOURCE_ROOT/pyproject.toml" ] ||
        die "source directory has no pyproject.toml: $XFETCH_SOURCE_ROOT"
    [ -f "$XFETCH_SOURCE_ROOT/SKILL.md" ] ||
        die "source directory has no SKILL.md: $XFETCH_SOURCE_ROOT"
    XFETCH_REVISION=$revision
else
    XFETCH_COMMIT_JSON=$XFETCH_TMP_DIR/commit.json
    XFETCH_ARCHIVE=$XFETCH_TMP_DIR/source.tar.gz
    XFETCH_EXTRACT_DIR=$XFETCH_TMP_DIR/source
    xfetch_fetch "$XFETCH_COMMIT_URL" "$XFETCH_COMMIT_JSON" ||
        die 'could not resolve the main revision'
    XFETCH_REVISION=$(awk -F '"' '/"sha"[[:space:]]*:/ { print $4; exit }' "$XFETCH_COMMIT_JSON")
    case $XFETCH_REVISION in
        ''|*[!0-9A-Fa-f]*) die 'GitHub returned an invalid main revision' ;;
    esac
    [ "$(printf '%s' "$XFETCH_REVISION" | awk '{ print length }')" -eq 40 ] ||
        die 'GitHub returned a non-immutable main revision'
    xfetch_fetch "$XFETCH_REPOSITORY/archive/$XFETCH_REVISION.tar.gz" "$XFETCH_ARCHIVE" ||
        die 'could not download the source archive'
    mkdir "$XFETCH_EXTRACT_DIR"
    tar -xzf "$XFETCH_ARCHIVE" -C "$XFETCH_EXTRACT_DIR" ||
        die 'could not extract the source archive'
    XFETCH_SOURCE_ROOT=
    for XFETCH_CANDIDATE in "$XFETCH_EXTRACT_DIR"/*; do
        if [ -d "$XFETCH_CANDIDATE" ]; then
            [ -z "$XFETCH_SOURCE_ROOT" ] ||
                die 'the source archive has multiple roots'
            XFETCH_SOURCE_ROOT=$XFETCH_CANDIDATE
        fi
    done
    [ -n "$XFETCH_SOURCE_ROOT" ] || die 'the source archive has no root directory'
    [ -f "$XFETCH_SOURCE_ROOT/pyproject.toml" ] ||
        die 'the source archive has no pyproject.toml'
    [ -f "$XFETCH_SOURCE_ROOT/SKILL.md" ] ||
        die 'the source archive has no SKILL.md'
fi

XFETCH_VENV_DIR=$XFETCH_RUNTIME_ROOT/venv
XFETCH_EXECUTABLE=$XFETCH_VENV_DIR/bin/xfetch
XFETCH_MARKER_FILE=$XFETCH_TMP_DIR/marker
XFETCH_INSTALLATION_FILE=$XFETCH_TMP_DIR/INSTALLATION.md
XFETCH_RUNTIME_MANIFEST=$XFETCH_RUNTIME_ROOT/.xfetch-runtime
printf '%s\n' "$XFETCH_MARKER_VALUE" > "$XFETCH_MARKER_FILE"
{
    printf '%s\n' '# xfetch installation'
    printf '%s\n' ''
    printf '%s\n' '- executable: '"$XFETCH_EXECUTABLE"
    printf '%s\n' '- default content root: ~/xfetch-content'
    printf '%s\n' '- installed revision: '"$XFETCH_REVISION"
} > "$XFETCH_INSTALLATION_FILE"

xfetch_preflight_file() {
    XFETCH_DESTINATION=$1
    XFETCH_EXPECTED=$2
    if xfetch_path_exists "$XFETCH_DESTINATION"; then
        [ -f "$XFETCH_DESTINATION" ] ||
            die "managed path is not a file: $XFETCH_DESTINATION"
        xfetch_is_symlink "$XFETCH_DESTINATION" &&
            die "managed path is a symlink: $XFETCH_DESTINATION"
        cmp -s "$XFETCH_EXPECTED" "$XFETCH_DESTINATION" ||
            die "managed file was modified: $XFETCH_DESTINATION"
    fi
}

xfetch_checksum() {
    cksum "$1" | awk '{ print $1 ":" $2 }'
}

xfetch_runtime_preflight() {
    XFETCH_RUNTIME_READY=0
    if ! xfetch_path_exists "$XFETCH_RUNTIME_ROOT"; then
        return 0
    fi
    if ! xfetch_path_exists "$XFETCH_RUNTIME_MANIFEST"; then
        die "managed runtime has no runtime manifest: $XFETCH_RUNTIME_ROOT"
    fi
    [ -f "$XFETCH_RUNTIME_MANIFEST" ] ||
        die "runtime manifest is not a file: $XFETCH_RUNTIME_MANIFEST"
    xfetch_is_symlink "$XFETCH_RUNTIME_MANIFEST" &&
        die "runtime manifest is a symlink: $XFETCH_RUNTIME_MANIFEST"
    XFETCH_RUNTIME_FORMAT=$(sed -n '1p' "$XFETCH_RUNTIME_MANIFEST")
    [ "$XFETCH_RUNTIME_FORMAT" = xfetch-runtime-v1 ] ||
        die "managed runtime has an invalid manifest: $XFETCH_RUNTIME_MANIFEST"
    XFETCH_STORED_REVISION=$(sed -n '2s/^revision=//p' "$XFETCH_RUNTIME_MANIFEST")
    [ "$XFETCH_STORED_REVISION" = "$XFETCH_REVISION" ] ||
        die "managed runtime has a different revision: $XFETCH_RUNTIME_ROOT"
    XFETCH_STORED_EXECUTABLE=$(sed -n '3s/^executable=//p' "$XFETCH_RUNTIME_MANIFEST")
    [ "$XFETCH_STORED_EXECUTABLE" = "$XFETCH_EXECUTABLE" ] ||
        die "managed runtime has a different executable path: $XFETCH_RUNTIME_ROOT"
    XFETCH_STORED_CHECKSUM=$(sed -n '4s/^executable-checksum=//p' "$XFETCH_RUNTIME_MANIFEST")
    [ -n "$XFETCH_STORED_CHECKSUM" ] ||
        die "managed runtime has an incomplete manifest: $XFETCH_RUNTIME_MANIFEST"

    xfetch_path_exists "$XFETCH_EXECUTABLE" ||
        die "managed runtime executable is missing; inspect or remove the verified runtime and rerun"
    [ -f "$XFETCH_EXECUTABLE" ] ||
        die "managed executable is not a file: $XFETCH_EXECUTABLE"
    xfetch_is_symlink "$XFETCH_EXECUTABLE" &&
        die "managed executable is a symlink: $XFETCH_EXECUTABLE"
    [ -x "$XFETCH_EXECUTABLE" ] ||
        die "managed executable is not executable: $XFETCH_EXECUTABLE"
    XFETCH_ACTUAL_CHECKSUM=$(xfetch_checksum "$XFETCH_EXECUTABLE")
    [ "$XFETCH_ACTUAL_CHECKSUM" = "$XFETCH_STORED_CHECKSUM" ] ||
        die "managed executable was modified: $XFETCH_EXECUTABLE"
    "$XFETCH_EXECUTABLE" --help >/dev/null ||
        die "the managed xfetch executable failed its smoke check: $XFETCH_EXECUTABLE"
    XFETCH_RUNTIME_READY=1
}

case $agent in
    codex)
        xfetch_preflight_file "$XFETCH_CODEX_SKILL/SKILL.md" "$XFETCH_SOURCE_ROOT/SKILL.md"
        xfetch_preflight_file "$XFETCH_CODEX_SKILL/INSTALLATION.md" "$XFETCH_INSTALLATION_FILE"
        ;;
    claude)
        xfetch_preflight_file "$XFETCH_CLAUDE_SKILL/SKILL.md" "$XFETCH_SOURCE_ROOT/SKILL.md"
        xfetch_preflight_file "$XFETCH_CLAUDE_SKILL/INSTALLATION.md" "$XFETCH_INSTALLATION_FILE"
        ;;
    both)
        xfetch_preflight_file "$XFETCH_CODEX_SKILL/SKILL.md" "$XFETCH_SOURCE_ROOT/SKILL.md"
        xfetch_preflight_file "$XFETCH_CODEX_SKILL/INSTALLATION.md" "$XFETCH_INSTALLATION_FILE"
        xfetch_preflight_file "$XFETCH_CLAUDE_SKILL/SKILL.md" "$XFETCH_SOURCE_ROOT/SKILL.md"
        xfetch_preflight_file "$XFETCH_CLAUDE_SKILL/INSTALLATION.md" "$XFETCH_INSTALLATION_FILE"
        ;;
esac

xfetch_runtime_preflight

XFETCH_UV_BIN=$XFETCH_HOME_DIR/.local/bin/uv
if [ "$XFETCH_RUNTIME_READY" -eq 0 ]; then
    if xfetch_path_exists "$XFETCH_UV_BIN"; then
        [ -f "$XFETCH_UV_BIN" ] && [ -x "$XFETCH_UV_BIN" ] ||
            die "uv path is not an executable file: $XFETCH_UV_BIN"
    elif XFETCH_PATH_UV=$(command -v uv 2>/dev/null); then
        XFETCH_UV_BIN=$XFETCH_PATH_UV
    else
        XFETCH_UV_INSTALL_DIR=$XFETCH_HOME_DIR/.local/bin
        mkdir -p "$XFETCH_UV_INSTALL_DIR"
        XFETCH_UV_SCRIPT=$XFETCH_TMP_DIR/uv-install.sh
        xfetch_fetch "$XFETCH_UV_URL" "$XFETCH_UV_SCRIPT" ||
            die 'could not download the uv installer'
        (
            export UV_NO_MODIFY_PATH=1
            export UV_INSTALL_DIR="$XFETCH_UV_INSTALL_DIR"
            sh "$XFETCH_UV_SCRIPT"
        ) || die 'uv bootstrap failed'
        [ -f "$XFETCH_UV_BIN" ] && [ -x "$XFETCH_UV_BIN" ] ||
            die "uv bootstrap did not install $XFETCH_UV_BIN"
    fi
fi

XFETCH_RUNTIME_CREATED=0
XFETCH_CODEX_SKILL_CREATED=0
XFETCH_CLAUDE_SKILL_CREATED=0
if [ "$XFETCH_RUNTIME_READY" -eq 0 ] &&
    ! xfetch_path_exists "$XFETCH_RUNTIME_ROOT"; then
    XFETCH_RUNTIME_CREATED=1
fi
case $agent in
    codex)
        if ! xfetch_path_exists "$XFETCH_CODEX_SKILL"; then
            XFETCH_CODEX_SKILL_CREATED=1
        fi
        ;;
    claude)
        if ! xfetch_path_exists "$XFETCH_CLAUDE_SKILL"; then
            XFETCH_CLAUDE_SKILL_CREATED=1
        fi
        ;;
    both)
        if ! xfetch_path_exists "$XFETCH_CODEX_SKILL"; then
            XFETCH_CODEX_SKILL_CREATED=1
        fi
        if ! xfetch_path_exists "$XFETCH_CLAUDE_SKILL"; then
            XFETCH_CLAUDE_SKILL_CREATED=1
        fi
        ;;
esac

xfetch_cleanup() {
    XFETCH_STATUS=$?
    if [ "$XFETCH_STATUS" -ne 0 ]; then
        if [ "$XFETCH_RUNTIME_CREATED" -eq 1 ]; then
            rm -rf "$XFETCH_RUNTIME_ROOT"
        fi
        if [ "$XFETCH_CODEX_SKILL_CREATED" -eq 1 ]; then
            rm -rf "$XFETCH_CODEX_SKILL"
        fi
        if [ "$XFETCH_CLAUDE_SKILL_CREATED" -eq 1 ]; then
            rm -rf "$XFETCH_CLAUDE_SKILL"
        fi
    fi
    rm -rf "$XFETCH_TMP_DIR"
    trap - EXIT
    exit "$XFETCH_STATUS"
}
trap xfetch_cleanup EXIT

if [ "$XFETCH_RUNTIME_READY" -eq 0 ]; then
    mkdir -p "$XFETCH_RUNTIME_ROOT"
    if ! xfetch_path_exists "$XFETCH_RUNTIME_ROOT/$XFETCH_MARKER_NAME"; then
        cp "$XFETCH_MARKER_FILE" "$XFETCH_RUNTIME_ROOT/$XFETCH_MARKER_NAME"
    fi
    "$XFETCH_UV_BIN" venv --python 3.12 "$XFETCH_VENV_DIR" ||
        die 'could not create the Python 3.12 virtual environment'
    XFETCH_PYTHON_BIN=$XFETCH_VENV_DIR/bin/python
    [ -x "$XFETCH_PYTHON_BIN" ] ||
        die "uv did not create the venv interpreter: $XFETCH_PYTHON_BIN"
    "$XFETCH_UV_BIN" pip install --python "$XFETCH_PYTHON_BIN" "$XFETCH_SOURCE_ROOT" ||
        die 'could not install xfetch into the virtual environment'
    [ -x "$XFETCH_EXECUTABLE" ] ||
        die "the xfetch executable was not installed: $XFETCH_EXECUTABLE"
    "$XFETCH_EXECUTABLE" --help >/dev/null ||
        die "the xfetch executable failed its smoke check: $XFETCH_EXECUTABLE"
    XFETCH_EXECUTABLE_CHECKSUM=$(xfetch_checksum "$XFETCH_EXECUTABLE")
    {
        printf '%s\n' xfetch-runtime-v1
        printf '%s\n' revision="$XFETCH_REVISION"
        printf '%s\n' executable="$XFETCH_EXECUTABLE"
        printf '%s\n' executable-checksum="$XFETCH_EXECUTABLE_CHECKSUM"
    } > "$XFETCH_RUNTIME_MANIFEST"
fi

xfetch_install_skill() {
    XFETCH_SKILL_DIRECTORY=$1
    mkdir -p "$XFETCH_SKILL_DIRECTORY"
    if ! xfetch_path_exists "$XFETCH_SKILL_DIRECTORY/$XFETCH_MARKER_NAME"; then
        cp "$XFETCH_MARKER_FILE" "$XFETCH_SKILL_DIRECTORY/$XFETCH_MARKER_NAME"
    fi
    cp "$XFETCH_SOURCE_ROOT/SKILL.md" "$XFETCH_SKILL_DIRECTORY/SKILL.md"
    cp "$XFETCH_INSTALLATION_FILE" "$XFETCH_SKILL_DIRECTORY/INSTALLATION.md"
}

case $agent in
    codex) xfetch_install_skill "$XFETCH_CODEX_SKILL" ;;
    claude) xfetch_install_skill "$XFETCH_CLAUDE_SKILL" ;;
    both)
        xfetch_install_skill "$XFETCH_CODEX_SKILL"
        xfetch_install_skill "$XFETCH_CLAUDE_SKILL"
        ;;
esac

printf 'xfetch runtime: %s (revision %s)\n' "$XFETCH_EXECUTABLE" "$XFETCH_REVISION"
printf 'runtime manifest: %s\n' "$XFETCH_RUNTIME_MANIFEST"
case $agent in
    codex)
        printf 'codex skill: %s\n' "$XFETCH_CODEX_SKILL"
        printf '%s\n' 'first use (Codex): invoke $xfetch; for a local URL ask "save this URL locally: https://example.com/"'
        ;;
    claude)
        printf 'claude skill: %s\n' "$XFETCH_CLAUDE_SKILL"
        printf '%s\n' 'first use (Claude Code): invoke /xfetch; for a local URL ask "save this URL locally: https://example.com/"'
        ;;
    both)
        printf 'codex skill: %s\n' "$XFETCH_CODEX_SKILL"
        printf 'claude skill: %s\n' "$XFETCH_CLAUDE_SKILL"
        printf '%s\n' 'first use (Codex): invoke $xfetch; (Claude Code): invoke /xfetch; for a local URL ask "save this URL locally: https://example.com/"'
        ;;
esac
