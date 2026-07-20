from population.factory import build_parser
from population.repository import PopulationRepository
from population.service import PopulationService


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: main.py <get_data|print_data>")

    command = sys.argv[1]
    service = PopulationService(build_parser(), PopulationRepository())

    if command == "get_data":
        service.load_data_sync()
    elif command == "print_data":
        service.print_summary_sync()
    else:
        raise SystemExit("Usage: main.py <get_data|print_data>")


if __name__ == "__main__":
    main()
