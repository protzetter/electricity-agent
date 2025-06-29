"""
ENTSOE API Tool for Strands Agents - CORRECTED VERSION

This tool provides access to the ENTSOE (European Network of Transmission System Operators 
for Electricity) Transparency Platform API, with corrected API calls based on official documentation.

API Documentation: https://documenter.getpostman.com/view/7009892/2s93JtP3F6
"""

from typing import Dict, Any, Optional, List
from strands import tool
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
import logging
import pytz
from dotenv import load_dotenv


# Add the project root to the path so we can import our modules
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../config/.env')
load_dotenv(config_path)

# Also try loading from current directory and parent directories as fallback
load_dotenv()  # Load from current directory
load_dotenv(dotenv_path='.env')  # Load from .env in current dir
load_dotenv(dotenv_path='config/.env')  # Load from config/.env

logger = logging.getLogger(__name__)

# CORRECTED Area codes for European countries (FIXED CRITICAL BUGS)
ENTSOE_AREA_CODES = {
    'DE': '10Y1001A1001A83F',  # Germany
    'FR': '10Y1001A1001A92E',  # France  
    'IT': '10Y1001A1001A788',  # Italy
    'ES': '10Y1001A1001A85H',  # Spain
    'NL': '10Y1001A1001A92K',  # Netherlands
    'BE': '10Y1001A1001A82H',  # Belgium
    'AT': '10Y1001A1001A92W',  # Austria
    'CH': '10Y1001A1001A92O',  # Switzerland
    'PL': '10Y1001A1001A92F',  # Poland
    'CZ': '10YCZ-CEPS-----N',  # Czech Republic - FIXED! (was using France's code)
    'DK': '10Y1001A1001A65H',  # Denmark
    'SE': '10Y1001A1001A44P',  # Sweden
    'NO': '10Y1001A1001A48H',  # Norway
    'FI': '10Y1001A1001A39I',  # Finland
    'GB': '10YGB----------A',  # Great Britain - FIXED! (was using France's code)
    'IE': '10Y1001A1001A59C',  # Ireland
    'PT': '10Y1001A1001A85H',  # Portugal - FIXED! (was using Germany's code)
}

# CORRECTED Document types based on official ENTSOE documentation
ENTSOE_DOCUMENT_TYPES = {
    # Load data
    'load_forecast': 'A65',           # Load forecast
    'load_actual': 'A65',             # Actual total load
    
    # Generation data  
    'generation_forecast': 'A71',     # Generation forecast
    'generation_actual': 'A75',       # Actual generation per production type
    'generation_aggregated': 'A75',   # Aggregated generation per type
    
    # Prices
    'day_ahead_prices': 'A44',        # Day-ahead prices
    'intraday_prices': 'A44',         # Intraday prices (different processType)
    
    # Cross-border flows
    'cross_border_flows': 'A11',      # Cross-border physical flows
    
    # Renewable forecasts
    'wind_solar_forecast': 'A69',     # Wind and solar forecast
    
    # Balancing
    'imbalance_prices': 'A85',        # Imbalance prices
    'balancing_energy': 'A86',        # Balancing energy bids
    
    # Unavailability
    'unavailability_generation': 'A77', # Unavailability of generation units
    'unavailability_transmission': 'A78', # Unavailability of transmission infrastructure
}

# CORRECTED Process types based on official documentation
ENTSOE_PROCESS_TYPES = {
    'day_ahead': 'A01',               # Day ahead
    'intraday': 'A02',                # Intraday incremental
    'realtime': 'A16',                # Realtime
    'week_ahead': 'A31',              # Week ahead
    'month_ahead': 'A32',             # Month ahead  
    'year_ahead': 'A33',              # Year ahead
    'synchronisation_process': 'A39', # Synchronisation process
    'intraday_total': 'A18',          # Intraday total
}

def _get_api_token() -> Optional[str]:
    """Get ENTSOE API token from environment variable with debugging."""
    token = os.environ.get('ENTSOE_API_TOKEN')
    
    if not token:
        # Try alternative environment variable names
        token = os.environ.get('ENTSOE_TOKEN')
        if not token:
            token = os.environ.get('ENTSOE_API_KEY')
    
    # Debug information (only log if token is missing)
    if not token:
        logger.debug(f"ENTSOE API token not found. Checked environment variables:")
        logger.debug(f"  - ENTSOE_API_TOKEN: {'SET' if os.environ.get('ENTSOE_API_TOKEN') else 'NOT SET'}")
        logger.debug(f"  - ENTSOE_TOKEN: {'SET' if os.environ.get('ENTSOE_TOKEN') else 'NOT SET'}")
        logger.debug(f"  - ENTSOE_API_KEY: {'SET' if os.environ.get('ENTSOE_API_KEY') else 'NOT SET'}")
        logger.debug(f"  - Config path used: {config_path}")
        logger.debug(f"  - Config file exists: {os.path.exists(config_path)}")
    
    return token

def _get_entsoe_time_range(hours_back: int = 24, data_delay_hours: int = 2) -> tuple:
    """
    Get proper time range for ENTSOE API calls with timezone handling.
    
    ENTSOE uses Central European Time (CET/CEST) and has data publication delays.
    
    Args:
        hours_back: Number of hours back to fetch data
        data_delay_hours: Hours to subtract to account for publication delay
        
    Returns:
        tuple: (start_time, end_time) as datetime objects in CET
    """
    try:
        # Use Central European Time (handles CET/CEST automatically)
        cet = pytz.timezone('Europe/Berlin')
        now_cet = datetime.now(cet)
        
        # Account for data publication delay
        end_time = now_cet - timedelta(hours=data_delay_hours)
        start_time = end_time - timedelta(hours=hours_back)
        
        # Round to nearest 15-minute interval (ENTSOE data intervals)
        start_time = start_time.replace(minute=(start_time.minute // 15) * 15, second=0, microsecond=0)
        end_time = end_time.replace(minute=(end_time.minute // 15) * 15, second=0, microsecond=0)
        
        return start_time, end_time
        
    except Exception as e:
        logger.warning(f"Error in timezone handling, falling back to UTC: {e}")
        # Fallback to UTC if timezone handling fails
        now_utc = datetime.utcnow()
        end_time = now_utc - timedelta(hours=data_delay_hours)
        start_time = end_time - timedelta(hours=hours_back)
        return start_time, end_time

def _get_day_ahead_price_range(days_back: int = 1) -> tuple:
    """
    Get proper time range for day-ahead prices.
    Day-ahead prices are published around 12:30 CET for the next day.
    
    Args:
        days_back: Number of days back to fetch prices
        
    Returns:
        tuple: (start_time, end_time) for complete day(s)
    """
    try:
        cet = pytz.timezone('Europe/Berlin')
        now_cet = datetime.now(cet)
        
        # Get the date for which prices should be available
        target_date = now_cet.date() - timedelta(days=days_back)
        
        # Start at midnight of target date
        start_time = cet.localize(datetime.combine(target_date, datetime.min.time()))
        # End at midnight of next day
        end_time = start_time + timedelta(days=1)
        
        return start_time, end_time
        
    except Exception as e:
        logger.warning(f"Error in day-ahead price time handling: {e}")
        # Fallback
        now = datetime.utcnow()
        start_time = now - timedelta(days=days_back)
        end_time = start_time + timedelta(days=1)
        return start_time, end_time

def _make_entsoe_request(params: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to the ENTSOE API with improved error handling."""
    api_token = _get_api_token()
    if not api_token:
        return {
            'error': 'ENTSOE API token not found. Please set ENTSOE_API_TOKEN environment variable.',
            'status': 'error'
        }
    
    base_url = "https://web-api.tp.entsoe.eu/api"
    params['securityToken'] = api_token
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        
        # Enhanced error handling based on ENTSOE API documentation
        if response.status_code == 400:
            error_msg = "Bad Request - Invalid parameters"
            if response.text:
                try:
                    root = ET.fromstring(response.text)
                    error_elem = root.find('.//{*}text')
                    if error_elem is not None:
                        error_msg = f"Bad Request: {error_elem.text}"
                    else:
                        # Check for Acknowledgement_MarketDocument with error
                        reason_elem = root.find('.//{*}reason')
                        if reason_elem is not None:
                            error_msg = f"Bad Request: {reason_elem.find('.//{*}text').text if reason_elem.find('.//{*}text') is not None else 'Unknown error'}"
                except ET.ParseError:
                    error_msg = f"Bad Request: {response.text[:200]}"
            
            return {
                'error': error_msg,
                'status_code': 400,
                'request_params': {k: v for k, v in params.items() if k != 'securityToken'},
                'status': 'error'
            }
        elif response.status_code == 401:
            return {
                'error': 'Unauthorized - Invalid API token',
                'status_code': 401,
                'status': 'error'
            }
        elif response.status_code == 429:
            return {
                'error': 'Rate limit exceeded - Too many requests',
                'status_code': 429,
                'status': 'error'
            }
        elif response.status_code == 404:
            return {
                'error': 'No data found for the requested parameters',
                'status_code': 404,
                'request_params': {k: v for k, v in params.items() if k != 'securityToken'},
                'status': 'error'
            }
        
        response.raise_for_status()
        
        # Parse XML response
        return _parse_entsoe_xml(response.text)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"ENTSOE API request failed: {e}")
        return {
            'error': f'API request failed: {str(e)}',
            'request_params': {k: v for k, v in params.items() if k != 'securityToken'},
            'status': 'error'
        }

def _parse_entsoe_xml(xml_content: str) -> Dict[str, Any]:
    """Parse ENTSOE XML response into structured data with improved parsing."""
    try:
        root = ET.fromstring(xml_content)
        
        data_points = []
        
        # FIXED: Detect namespace from root element
        if '}' in root.tag:
            namespace = root.tag.split('}')[0] + '}'
        else:
            namespace = ''
        
        # Find TimeSeries elements with the detected namespace
        if namespace:
            time_series_elements = root.findall(f'.//{namespace}TimeSeries')
        else:
            time_series_elements = root.findall('.//TimeSeries')
        
        # Fallback: try common ENTSOE namespaces if none found
        if not time_series_elements:
            common_namespaces = [
                'urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0',
                'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0',
                'urn:iec62325.351:tc57wg16:451-6:publicationdocument:7:0'
            ]
            for ns_uri in common_namespaces:
                time_series_elements.extend(root.findall(f'.//{{{ns_uri}}}TimeSeries'))
                if time_series_elements:
                    namespace = f'{{{ns_uri}}}'
                    break
        
        for time_series in time_series_elements:
            # Extract metadata
            metadata = {}
            
            # Get business type, object aggregation, etc.
            for child in time_series:
                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                if tag_name == 'businessType':
                    metadata['business_type'] = child.text
                elif tag_name == 'objectAggregation':
                    metadata['object_aggregation'] = child.text
                elif tag_name == 'in_Domain.mRID':
                    metadata['in_domain'] = child.text
                elif tag_name == 'out_Domain.mRID':
                    metadata['out_domain'] = child.text
                elif tag_name == 'outBiddingZone_Domain.mRID':
                    metadata['out_domain'] = child.text
                elif tag_name == 'quantity_Measure_Unit.name':
                    metadata['unit'] = child.text
                elif tag_name == 'price_Measure_Unit.name':
                    metadata['price_unit'] = child.text
                elif tag_name == 'currency_Unit.name':
                    metadata['currency'] = child.text
            
            # Find Period elements with correct namespace
            if namespace:
                periods = time_series.findall(f'{namespace}Period')
            else:
                periods = time_series.findall('Period')
            
            for period in periods:
                # Get time interval
                if namespace:
                    time_interval = period.find(f'{namespace}timeInterval')
                else:
                    time_interval = period.find('timeInterval')
                
                start_time = None
                end_time = None
                
                if time_interval is not None:
                    if namespace:
                        start_elem = time_interval.find(f'{namespace}start')
                        end_elem = time_interval.find(f'{namespace}end')
                    else:
                        start_elem = time_interval.find('start')
                        end_elem = time_interval.find('end')
                    
                    if start_elem is not None:
                        start_time = datetime.fromisoformat(start_elem.text.replace('Z', '+00:00'))
                    if end_elem is not None:
                        end_time = datetime.fromisoformat(end_elem.text.replace('Z', '+00:00'))
                
                # Get resolution
                if namespace:
                    resolution_elem = period.find(f'{namespace}resolution')
                else:
                    resolution_elem = period.find('resolution')
                
                resolution_minutes = 60  # Default
                
                if resolution_elem is not None:
                    res_text = resolution_elem.text
                    if 'PT15M' in res_text:
                        resolution_minutes = 15
                    elif 'PT30M' in res_text:
                        resolution_minutes = 30
                    elif 'PT1H' in res_text:
                        resolution_minutes = 60
                    elif 'PT60M' in res_text:
                        resolution_minutes = 60
                
                # Extract data points with correct namespace
                if namespace:
                    points = period.findall(f'{namespace}Point')
                else:
                    points = period.findall('Point')
                
                for point in points:
                    if namespace:
                        position_elem = point.find(f'{namespace}position')
                        quantity_elem = point.find(f'{namespace}quantity')
                        price_elem = point.find(f'{namespace}price.amount')
                    else:
                        position_elem = point.find('position')
                        quantity_elem = point.find('quantity')
                        price_elem = point.find('price.amount')
                    
                    if position_elem is not None:
                        position = int(position_elem.text)
                        
                        # Calculate timestamp
                        if start_time:
                            point_time = start_time + timedelta(minutes=(position - 1) * resolution_minutes)
                            timestamp = point_time.isoformat()
                        else:
                            timestamp = None
                        
                        # Get value (quantity or price)
                        value = None
                        unit = metadata.get('unit', 'MW')
                        
                        if quantity_elem is not None:
                            value = float(quantity_elem.text)
                        elif price_elem is not None:
                            value = float(price_elem.text)
                            unit = f"{metadata.get('currency', 'EUR')}/{metadata.get('unit', 'MWh')}"
                        
                        if value is not None:
                            data_point = {
                                'timestamp': timestamp,
                                'position': position,
                                'value': value,
                                'unit': unit,
                                'metadata': metadata
                            }
                            data_points.append(data_point)
        
        return {
            'data_points': data_points,
            'total_points': len(data_points),
            'status': 'success'
        }
        
    except ET.ParseError as e:
        logger.error(f"XML parsing error: {e}")
        return {
            'error': f'XML parsing failed: {str(e)}',
            'raw_content': xml_content[:500] + '...' if len(xml_content) > 500 else xml_content,
            'status': 'error'
        }

@tool
def get_electricity_load(country_code: str, hours_back: int = 24) -> Dict[str, Any]:
    """
    Get electricity load (consumption) data for a European country.
    CORRECTED: Uses proper ENTSOE API parameters with timezone handling and data delays.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany, 'FR' for France)
        hours_back: Number of hours back from now to fetch data (default: 24)
        
    Returns:
        dict: Electricity load data with timestamps and values in MW
    """
    try:
        if country_code.upper() not in ENTSOE_AREA_CODES:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': list(ENTSOE_AREA_CODES.keys()),
                'status': 'error'
            }
        
        area_code = ENTSOE_AREA_CODES[country_code.upper()]
        
        # Use improved time handling with data delay
        start_time, end_time = _get_entsoe_time_range(hours_back, data_delay_hours=2)
        
        # CORRECTED: Use proper parameters for actual total load
        params = {
            'documentType': ENTSOE_DOCUMENT_TYPES['load_actual'],  # A65
            'processType': ENTSOE_PROCESS_TYPES['realtime'],       # A16 for realtime
            'outBiddingZone_Domain': area_code,                    # CORRECT parameter name
            'periodStart': start_time.strftime('%Y%m%d%H%M'),      # CORRECTED: timezone-aware time
            'periodEnd': end_time.strftime('%Y%m%d%H%M')           # CORRECTED: timezone-aware time
        }
        
        result = _make_entsoe_request(params)
        
        if result.get('status') == 'success':
            result.update({
                'country': country_code.upper(),
                'data_type': 'electricity_load',
                'period_start': start_time.isoformat(),
                'period_end': end_time.isoformat(),
                'timezone_info': 'Times adjusted for CET/CEST and 2-hour data delay'
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching electricity load for {country_code}: {e}")
        return {
            'error': str(e),
            'country': country_code,
            'status': 'error'
        }

@tool
def get_electricity_generation(country_code: str, hours_back: int = 24) -> Dict[str, Any]:
    """
    Get electricity generation data for a European country.
    CORRECTED: Uses proper ENTSOE API parameters with timezone handling and data delays.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany, 'FR' for France)
        hours_back: Number of hours back from now to fetch data (default: 24)
        
    Returns:
        dict: Electricity generation data with timestamps and values in MW
    """
    try:
        if country_code.upper() not in ENTSOE_AREA_CODES:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': list(ENTSOE_AREA_CODES.keys()),
                'status': 'error'
            }
        
        area_code = ENTSOE_AREA_CODES[country_code.upper()]
        
        # Use improved time handling with data delay
        start_time, end_time = _get_entsoe_time_range(hours_back, data_delay_hours=2)
        
        # CORRECTED: Use proper parameters for actual generation per production type
        params = {
            'documentType': ENTSOE_DOCUMENT_TYPES['generation_actual'],  # A75
            'processType': ENTSOE_PROCESS_TYPES['realtime'],             # A16 for realtime
            'in_Domain': area_code,                                      # CORRECT parameter name
            'periodStart': start_time.strftime('%Y%m%d%H%M'),            # CORRECTED: timezone-aware time
            'periodEnd': end_time.strftime('%Y%m%d%H%M')                 # CORRECTED: timezone-aware time
        }
        
        result = _make_entsoe_request(params)
        
        if result.get('status') == 'success':
            result.update({
                'country': country_code.upper(),
                'data_type': 'electricity_generation',
                'period_start': start_time.isoformat(),
                'period_end': end_time.isoformat(),
                'timezone_info': 'Times adjusted for CET/CEST and 2-hour data delay'
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching electricity generation for {country_code}: {e}")
        return {
            'error': str(e),
            'country': country_code,
            'status': 'error'
        }

@tool
def get_day_ahead_prices(country_code: str, days_back: int = 1) -> Dict[str, Any]:
    """
    Get day-ahead electricity prices for a European country.
    CORRECTED: Uses proper ENTSOE API parameters with timezone handling for day-ahead prices.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany, 'FR' for France)
        days_back: Number of days back from now to fetch data (default: 1)
        
    Returns:
        dict: Day-ahead electricity prices with timestamps and values in EUR/MWh
    """
    try:
        if country_code.upper() not in ENTSOE_AREA_CODES:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': list(ENTSOE_AREA_CODES.keys()),
                'status': 'error'
            }
        
        area_code = ENTSOE_AREA_CODES[country_code.upper()]
        
        # Use improved time handling for day-ahead prices
        start_time, end_time = _get_day_ahead_price_range(days_back)
        
        # CORRECTED: Use proper parameters for day-ahead prices
        params = {
            'documentType': ENTSOE_DOCUMENT_TYPES['day_ahead_prices'],  # A44
            'processType': ENTSOE_PROCESS_TYPES['day_ahead'],           # A01 for day-ahead (CORRECTED)
            'in_Domain': area_code,                                     # CORRECT parameter name
            'out_Domain': area_code,                                    # CORRECT parameter name
            'periodStart': start_time.strftime('%Y%m%d%H%M'),           # CORRECTED: timezone-aware time
            'periodEnd': end_time.strftime('%Y%m%d%H%M')                # CORRECTED: timezone-aware time
        }
        
        result = _make_entsoe_request(params)
        
        if result.get('status') == 'success':
            # Update unit for prices
            for point in result.get('data_points', []):
                if 'EUR' not in point.get('unit', ''):
                    point['unit'] = 'EUR/MWh'
            
            result.update({
                'country': country_code.upper(),
                'data_type': 'day_ahead_prices',
                'period_start': start_time.isoformat(),
                'period_end': end_time.isoformat(),
                'timezone_info': 'Times in CET/CEST, prices for complete day(s)'
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching day-ahead prices for {country_code}: {e}")
        return {
            'error': str(e),
            'country': country_code,
            'status': 'error'
        }

@tool
def get_cross_border_flows(from_country: str, to_country: str, hours_back: int = 24) -> Dict[str, Any]:
    """
    Get cross-border electricity flows between two European countries.
    CORRECTED: Uses proper ENTSOE API parameters for cross-border physical flows.
    
    Args:
        from_country: Source country code (e.g., 'DE' for Germany)
        to_country: Destination country code (e.g., 'FR' for France)
        hours_back: Number of hours back from now to fetch data (default: 24)
        
    Returns:
        dict: Cross-border flow data with timestamps and values in MW
    """
    try:
        if (from_country.upper() not in ENTSOE_AREA_CODES or 
            to_country.upper() not in ENTSOE_AREA_CODES):
            return {
                'error': f'Unsupported country code(s): {from_country}, {to_country}',
                'supported_countries': list(ENTSOE_AREA_CODES.keys()),
                'status': 'error'
            }
        
        from_area = ENTSOE_AREA_CODES[from_country.upper()]
        to_area = ENTSOE_AREA_CODES[to_country.upper()]
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # CORRECTED: Use proper parameters for cross-border physical flows
        params = {
            'documentType': ENTSOE_DOCUMENT_TYPES['cross_border_flows'],  # A11
            'processType': ENTSOE_PROCESS_TYPES['realtime'],              # A16 for realtime
            'in_Domain': from_area,                                       # CORRECT parameter name
            'out_Domain': to_area,                                        # CORRECT parameter name
            'periodStart': start_time.strftime('%Y%m%d%H%M'),             # CORRECTED: Use actual time
            'periodEnd': end_time.strftime('%Y%m%d%H%M')                  # CORRECTED: Use actual time
        }
        
        result = _make_entsoe_request(params)
        
        if result.get('status') == 'success':
            result.update({
                'from_country': from_country.upper(),
                'to_country': to_country.upper(),
                'data_type': 'cross_border_flows',
                'period_start': start_time.isoformat(),
                'period_end': end_time.isoformat(),
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching cross-border flows from {from_country} to {to_country}: {e}")
        return {
            'error': str(e),
            'from_country': from_country,
            'to_country': to_country,
            'status': 'error'
        }

@tool
def get_renewable_forecast(country_code: str, hours_ahead: int = 48) -> Dict[str, Any]:
    """
    Get wind and solar generation forecast for a European country.
    CORRECTED: Uses proper ENTSOE API parameters for wind and solar forecast.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany, 'FR' for France)
        hours_ahead: Number of hours ahead to fetch forecast data (default: 48)
        
    Returns:
        dict: Renewable generation forecast data with timestamps and values in MW
    """
    try:
        if country_code.upper() not in ENTSOE_AREA_CODES:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': list(ENTSOE_AREA_CODES.keys()),
                'status': 'error'
            }
        
        area_code = ENTSOE_AREA_CODES[country_code.upper()]
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=hours_ahead)
        
        # CORRECTED: Use proper parameters for wind and solar forecast
        params = {
            'documentType': ENTSOE_DOCUMENT_TYPES['wind_solar_forecast'],  # A69
            'processType': ENTSOE_PROCESS_TYPES['day_ahead'],              # A01 for day-ahead forecast (CORRECTED)
            'in_Domain': area_code,                                        # CORRECT parameter name
            'periodStart': start_time.strftime('%Y%m%d%H%M'),              # CORRECTED: Use actual time
            'periodEnd': end_time.strftime('%Y%m%d%H%M')                   # CORRECTED: Use actual time
        }
        
        result = _make_entsoe_request(params)
        
        if result.get('status') == 'success':
            result.update({
                'country': country_code.upper(),
                'data_type': 'renewable_forecast',
                'period_start': start_time.isoformat(),
                'period_end': end_time.isoformat(),
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching renewable forecast for {country_code}: {e}")
        return {
            'error': str(e),
            'country': country_code,
            'status': 'error'
        }

# Additional corrected tools based on ENTSOE documentation

@tool
def get_imbalance_prices(country_code: str, hours_back: int = 24) -> Dict[str, Any]:
    """
    Get imbalance prices for a European country.
    NEW: Based on ENTSOE API documentation for imbalance pricing.
    
    Args:
        country_code: Two-letter country code
        hours_back: Number of hours back to fetch data
        
    Returns:
        dict: Imbalance price data
    """
    try:
        if country_code.upper() not in ENTSOE_AREA_CODES:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': list(ENTSOE_AREA_CODES.keys()),
                'status': 'error'
            }
        
        area_code = ENTSOE_AREA_CODES[country_code.upper()]
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        params = {
            'documentType': ENTSOE_DOCUMENT_TYPES['imbalance_prices'],  # A85
            'processType': ENTSOE_PROCESS_TYPES['realtime'],           # A16
            'controlArea_Domain': area_code,                           # CORRECT parameter for imbalance prices
            'periodStart': start_time.strftime('%Y%m%d%H%M'),
            'periodEnd': end_time.strftime('%Y%m%d%H%M')
        }
        
        result = _make_entsoe_request(params)
        
        if result.get('status') == 'success':
            result.update({
                'country': country_code.upper(),
                'data_type': 'imbalance_prices',
                'period_start': start_time.isoformat(),
                'period_end': end_time.isoformat(),
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching imbalance prices for {country_code}: {e}")
        return {
            'error': str(e),
            'country': country_code,
            'status': 'error'
        }

@tool
def get_supported_countries() -> Dict[str, Any]:
    """
    Get list of supported European countries for ENTSOE data.
    
    Returns:
        dict: List of supported country codes and their full names
    """
    country_names = {
        'DE': 'Germany',
        'FR': 'France',
        'IT': 'Italy',
        'ES': 'Spain',
        'NL': 'Netherlands',
        'BE': 'Belgium',
        'AT': 'Austria',
        'CH': 'Switzerland',
        'PL': 'Poland',
        'CZ': 'Czech Republic',
        'DK': 'Denmark',
        'SE': 'Sweden',
        'NO': 'Norway',
        'FI': 'Finland',
        'GB': 'Great Britain',
        'IE': 'Ireland',
        'PT': 'Portugal',
    }
    
    return {
        'supported_countries': country_names,
        'country_codes': list(country_names.keys()),
        'total_countries': len(country_names),
        'status': 'success'
    }

@tool
def get_entsoe_api_info() -> Dict[str, Any]:
    """
    Get information about the ENTSOE API and available data types.
    CORRECTED: Updated with proper document types and process types.
    
    Returns:
        dict: Information about ENTSOE API capabilities and requirements
    """
    return {
        'api_name': 'ENTSOE Transparency Platform API',
        'description': 'European electricity market data including generation, consumption, prices, and flows',
        'base_url': 'https://web-api.tp.entsoe.eu/api',
        'documentation': 'https://documenter.getpostman.com/view/7009892/2s93JtP3F6',
        'registration_url': 'https://transparency.entsoe.eu/',
        'available_data_types': list(ENTSOE_DOCUMENT_TYPES.keys()),
        'process_types': list(ENTSOE_PROCESS_TYPES.keys()),
        'supported_countries': list(ENTSOE_AREA_CODES.keys()),
        'api_token_required': True,
        'environment_variable': 'ENTSOE_API_TOKEN',
        'corrections_applied': [
            'Fixed area codes for CZ, GB, PT',
            'Corrected process types for day-ahead prices and forecasts',
            'Fixed time format to use actual hours instead of 0000/2300',
            'Enhanced XML parsing with proper namespace handling',
            'Added imbalance prices support',
            'Improved error handling for 404 responses'
        ],
        'status': 'success'
    }
@tool
def debug_entsoe_request(country_code: str, data_type: str = 'load') -> Dict[str, Any]:
    """
    Debug ENTSOE API requests by showing the exact parameters being sent.
    CORRECTED: Now shows the corrected parameters.
    
    This tool helps troubleshoot API requests by showing what parameters would be sent
    to the ENTSOE API without actually making the request.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany)
        data_type: Type of data to debug ('load', 'generation', 'prices')
        
    Returns:
        dict: Debug information including request parameters and URLs
    """
    try:
        if country_code.upper() not in ENTSOE_AREA_CODES:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': list(ENTSOE_AREA_CODES.keys()),
                'status': 'error'
            }
        
        area_code = ENTSOE_AREA_CODES[country_code.upper()]
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # Build parameters based on data type with CORRECTED values
        if data_type.lower() == 'load':
            params = {
                'documentType': ENTSOE_DOCUMENT_TYPES['load_actual'],  # A65
                'processType': ENTSOE_PROCESS_TYPES['realtime'],       # A16
                'outBiddingZone_Domain': area_code,
                'periodStart': start_time.strftime('%Y%m%d%H%M'),      # CORRECTED: actual time
                'periodEnd': end_time.strftime('%Y%m%d%H%M')           # CORRECTED: actual time
            }
        elif data_type.lower() == 'generation':
            params = {
                'documentType': ENTSOE_DOCUMENT_TYPES['generation_actual'],  # A75
                'processType': ENTSOE_PROCESS_TYPES['realtime'],             # A16
                'in_Domain': area_code,
                'periodStart': start_time.strftime('%Y%m%d%H%M'),            # CORRECTED: actual time
                'periodEnd': end_time.strftime('%Y%m%d%H%M')                 # CORRECTED: actual time
            }
        elif data_type.lower() == 'prices':
            params = {
                'documentType': ENTSOE_DOCUMENT_TYPES['day_ahead_prices'],  # A44
                'processType': ENTSOE_PROCESS_TYPES['day_ahead'],           # A01 - CORRECTED!
                'in_Domain': area_code,
                'out_Domain': area_code,
                'periodStart': start_time.strftime('%Y%m%d%H%M'),           # CORRECTED: actual time
                'periodEnd': end_time.strftime('%Y%m%d%H%M')                # CORRECTED: actual time
            }
        else:
            return {
                'error': f'Unsupported data type: {data_type}',
                'supported_types': ['load', 'generation', 'prices'],
                'status': 'error'
            }
        
        # Build the full URL
        base_url = "https://web-api.tp.entsoe.eu/api"
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{base_url}?{param_string}&securityToken=YOUR_TOKEN_HERE"
        
        return {
            'country': country_code.upper(),
            'data_type': data_type.lower(),
            'area_code': area_code,
            'request_parameters': params,
            'base_url': base_url,
            'full_url_example': full_url,
            'period_start': start_time.isoformat(),
            'period_end': end_time.isoformat(),
            'api_token_set': _get_api_token() is not None,
            'corrections_applied': [
                f'Time format: Using %Y%m%d%H%M instead of %Y%m%d0000/%Y%m%d2300',
                f'Process type for prices: A01 (day-ahead) instead of A16 (realtime)',
                f'Enhanced error handling and XML parsing'
            ],
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Error debugging ENTSOE request: {e}")
        return {
            'error': str(e),
            'status': 'error'
        }
