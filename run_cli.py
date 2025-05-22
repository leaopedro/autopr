import argparse

def create_pr(title):
    print(f"Creating a new PR with title: {title}")

def list_prs():
    print("Listing all PRs...")

def main():
    parser = argparse.ArgumentParser(description='AutoPR CLI')
    subparsers = parser.add_subparsers(dest='command')

    # Subparser for the 'create' command
    create_parser = subparsers.add_parser('create', help='Create a new PR')
    create_parser.add_argument('--title', required=True, help='Title of the new PR')

    # Subparser for the 'list' command
    list_parser = subparsers.add_parser('list', help='List all PRs')

    args = parser.parse_args()

    if args.command == 'create':
        create_pr(args.title)
    elif args.command == 'list':
        list_prs()

if __name__ == '__main__':
    main()