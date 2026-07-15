from django.core.management.base import BaseCommand
from food_analyzer.rag_engine import build_or_load_index

class Command(BaseCommand):
    help = 'Ingests text files in knowledge_base/ and builds the FAISS or TF-IDF vector index'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Force rebuild of the index',
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting knowledge base ingestion...")
        index_type, index_obj, chunks = build_or_load_index(force_rebuild=True)
        if index_type:
            self.stdout.write(self.style.SUCCESS(f"Successfully built {index_type} index with {len(chunks)} chunks."))
        else:
            self.stdout.write(self.style.ERROR("Failed to ingest knowledge base. Check files in knowledge_base/"))
