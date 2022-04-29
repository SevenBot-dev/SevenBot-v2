import git


def show_banner() -> None:
    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    print("--------------------------------")
    print("  SevenBot")
    print("    Hash: {}".format(sha))
    print("--------------------------------")
