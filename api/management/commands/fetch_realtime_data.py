"""
Management command to fetch real-time financial data from Financial Modeling Prep API
Usage:
    python manage.py fetch_realtime_data                # Fetch for all companies
    python manage.py fetch_realtime_data --symbol RELIANCE  # Fetch for specific company
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from companies.models import Company, RealtimeFinancialData
from api.realtime_service import RealtimeDataService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch real-time financial data from Financial Modeling Prep API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--symbol",
            type=str,
            help="Fetch data for specific stock symbol (e.g., RELIANCE)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force fetch even if recent data exists",
        )

    def handle(self, *args, **options):
        symbol = options.get("symbol", "").upper().strip()
        force = options.get("force", False)

        if symbol:
            # Fetch for specific company
            try:
                company = Company.objects.get(symbol=symbol)
                self.fetch_for_company(company, force)
            except Company.DoesNotExist:
                raise CommandError(f"Company with symbol {symbol} not found")
        else:
            # Fetch for all companies
            companies = Company.objects.all()
            self.stdout.write(
                self.style.SUCCESS(f"Fetching real-time data for {companies.count()} companies...")
            )
            
            success_count = 0
            error_count = 0
            
            for company in companies:
                try:
                    self.fetch_for_company(company, force)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error fetching data for {company.symbol}: {str(e)}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Completed: {success_count} success, {error_count} errors"
                )
            )

    def fetch_for_company(self, company, force=False):
        """Fetch and store real-time data for a company"""
        symbol = company.symbol

        # Check if recent data exists (within last 15 minutes)
        if not force:
            recent_data = RealtimeFinancialData.objects.filter(
                company=company,
                fetched_at__gte=timezone.now() - timezone.timedelta(minutes=15)
            ).first()
            
            if recent_data:
                self.stdout.write(
                    self.style.WARNING(f"⊘ {symbol}: Recent data exists (fetched at {recent_data.fetched_at})")
                )
                return

        # Fetch real-time data
        self.stdout.write(f"↓ Fetching data for {symbol}...", ending=" ")
        metrics = RealtimeDataService.get_company_realtime_snapshot(symbol)

        if not metrics:
            self.stdout.write(self.style.ERROR("✗ Failed"))
            raise CommandError(f"Failed to fetch real-time data for {symbol}")

        # Update or create RealtimeFinancialData record
        realtime_data, created = RealtimeFinancialData.objects.update_or_create(
            company=company,
            defaults={
                'revenue': metrics.get('revenue'),
                'net_income': metrics.get('net_income'),
                'operating_income': metrics.get('operating_income'),
                'gross_profit_margin': metrics.get('gross_profit_margin'),
                'operating_income_ratio': metrics.get('operating_income_ratio'),
                'net_income_ratio': metrics.get('net_income_ratio'),
                'eps': metrics.get('eps'),
                'ebitda': metrics.get('ebitda'),
                'total_assets': metrics.get('total_assets'),
                'total_liabilities': metrics.get('total_liabilities'),
                'total_equity': metrics.get('total_equity'),
                'current_assets': metrics.get('current_assets'),
                'current_liabilities': metrics.get('current_liabilities'),
                'operating_cash_flow': metrics.get('operating_cash_flow'),
                'free_cash_flow': metrics.get('free_cash_flow'),
                'capital_expenditure': metrics.get('capital_expenditure'),
                'pe_ratio': metrics.get('pe_ratio'),
                'roe': metrics.get('roe'),
                'roa': metrics.get('roa'),
                'debt_to_equity': metrics.get('debt_to_equity'),
                'current_ratio': metrics.get('current_ratio'),
                'quick_ratio': metrics.get('quick_ratio'),
                'dividend_yield': metrics.get('dividend_yield'),
                'income_statement_date': metrics.get('income_statement_date'),
                'balance_sheet_date': metrics.get('balance_sheet_date'),
                'cash_flow_date': metrics.get('cash_flow_date'),
            }
        )

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"✓ {action}"))
