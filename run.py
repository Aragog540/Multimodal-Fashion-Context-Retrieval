import argparse
import sys
from indexer.pipeline import run_indexing_pipeline
from retriever.cli import run_cli_search

def main():
    parser = argparse.ArgumentParser(
        description="Multimodal Fashion & Context Retrieval System",
        usage="python run.py <command> [<args>]"
    )
    parser.add_argument("command", choices=["index", "search"], help="Subcommand to run")
    args = parser.parse_args(sys.argv[1:2])
    
    if args.command == "index":
        # Parse indexer arguments
        idx_parser = argparse.ArgumentParser(description="Run Indexer Pipeline (Part A)")
        idx_parser.add_argument("--dir", default=r"c:\Users\swaro\Desktop\glance assgn\val_test2020\test", help="Path to images directory")
        idx_parser.add_argument("--db", default="fashion_search.db", help="Path to SQLite database")
        idx_parser.add_argument("--batch", type=int, default=16, help="Batch size for pipeline processing")
        idx_parser.add_argument("--limit", type=int, default=None, help="Limit number of images to index")
        
        idx_args = idx_parser.parse_args(sys.argv[2:])
        run_indexing_pipeline(
            dataset_dir=idx_args.dir,
            db_path=idx_args.db,
            batch_size=idx_args.batch,
            limit=idx_args.limit
        )
        
    elif args.command == "search":
        # Parse retriever arguments
        ret_parser = argparse.ArgumentParser(description="Run Retriever Search (Part B)")
        ret_parser.add_argument("query", type=str, help="Natural language search query")
        ret_parser.add_argument("-k", type=int, default=5, help="Number of top matching images to retrieve")
        ret_parser.add_argument("--db", default="fashion_search.db", help="Path to SQLite database")
        ret_parser.add_argument("--dir", default=r"c:\Users\swaro\Desktop\glance assgn\val_test2020\test", help="Path to images directory")
        ret_parser.add_argument("--show", action="store_true", help="Open the top matching image in default viewer")
        
        ret_args = ret_parser.parse_args(sys.argv[2:])
        run_cli_search(
            query=ret_args.query,
            k=ret_args.k,
            db_path=ret_args.db,
            dataset_dir=ret_args.dir,
            open_images=ret_args.show
        )

if __name__ == "__main__":
    main()
