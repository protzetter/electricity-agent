"""

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

# First, configure the root logger (this sets up the default handler)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
# Set the level to INFO (or DEBUG to see even more)
logger.setLevel(logging.INFO)

# CORRECTED Area codes for European countries (FIXED CRITICAL BUGS)
def _get_area_code(country_code: str) -> str:
    """Internal function to get ENTSOE area code from country code."""
    area_codes = {
        'DE': '10Y1001A1001A83F', 'FR': '10YFR-RTE------C', 'IT': '10YIT-GRTN-----B',
        'ES': '10YES-REE------0', 'NL': '10YNL----------L', 'BE': '10YBE----------2',
        'AT': '10YAT-APG------L', 'CH': '10YCH-SWISSGRIDZ', 'PL': '10YPL-AREA-----S',
        'CZ': '10YCZ-CEPS-----N', 'DK': '10Y1001A1001A65H', 'SE': '10YSE-1--------K',
        'NO': '10YNO-0--------C', 'FI': '10YFI-1--------U', 'GB': '10Y1001A1001A92E',
        'IE': '10YIE-1001A00010', 'PT': '10YPT-REN------W'
    }
    return area_codes.get(country_code.upper())

def _get_data_delay(country_code: str) -> int:
    """Internal function to get data delay for country."""
    delays = {
        'DE': 48, 'FR': 36, 'IT': 36, 'ES': 36, 'NL': 36, 'BE': 36,
        'AT': 48, 'CH': 36, 'PL': 36, 'CZ': 24, 'DK': 36, 'SE': 36,
        'NO': 36, 'FI': 36, 'GB': 36, 'IE': 36, 'PT': 36
    }
    return delays.get(country_code.upper(), 36)

def _get_supported_countries() -> List[str]:
    """Internal function to get list of supported countries."""
    return ['DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'CH', 'PL', 'CZ', 'DK', 'SE', 'NO', 'FI', 'GB', 'IE', 'PT']


# CORRECTED Document types based on official ENTSOE documentation
ENTSOE_DOCUMENT_TYPES = {
    # Load data
    'load_forecast': 'A65',           # Load forecast
    'load_actual': 'A65',             # Actual total load
    
    # Generation data  
    'generation_forecast': 'A71',     # Generation forecast
    'generation_actual': 'A75',       # Actual generation per production type
    'generation_aggregated': 'A75',   # Aggregated generation per type
    'actual_generation': 'A73',       # Actual generation (CORRECTED)
    'actual_generation_per_unit': 'A74', # Actual generation per generation unit
    
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
        
        # Check if this is an Acknowledgement_MarketDocument (error response)
        if 'Acknowledgement_MarketDocument' in root.tag:
            # Extract error information
            reason_elem = root.find('.//{*}Reason')
            if reason_elem is not None:
                code_elem = reason_elem.find('.//{*}code')
                text_elem = reason_elem.find('.//{*}text')
                
                error_code = code_elem.text if code_elem is not None else 'Unknown'
                error_text = text_elem.text if text_elem is not None else 'No error message'
                
                return {
                    'error': f'ENTSOE API Error {error_code}: {error_text}',
                    'error_code': error_code,
                    'data_points': [],
                    'total_points': 0,
                    'status': 'error'
                }
        
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
def get_electricity_load(country_code: str, hours_back: int = 6) -> Dict[str, Any]:
    """
    Get electricity load (consumption) data for a European country.
    FIXED: Uses proper country-specific data delays and improved error handling.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany, 'FR' for France)
        hours_back: Number of hours of data to fetch (default: 24)
        
    Returns:
        dict: Electricity load data with timestamps and values in MW
    """
    try:
        # Validate country code
        area_code = _get_area_code(country_code)
        if not area_code:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': _get_supported_countries(),
                'status': 'error'
            }
        

        
        # Get country-specific data delay
        data_delay = 0 #_get_data_delay(country_code)  # Default 36 hours
        
        # Calculate time range with proper delay
        cet = pytz.timezone('Europe/Berlin')
        now_cet = datetime.now(cet)
        
        # Apply country-specific data delay
        end_time = now_cet - timedelta(hours=data_delay)
        start_time = end_time - timedelta(hours=hours_back)
        
        # Round to start of hour for cleaner data
        start_time = start_time.replace(minute=0, second=0, microsecond=0)
        end_time = end_time.replace(minute=0, second=0, microsecond=0)
        
        # Build request parameters
        params = {
            'documentType': ENTSOE_DOCUMENT_TYPES['load_actual'],  # A65
            'processType': ENTSOE_PROCESS_TYPES['realtime'],       # A16
            'outBiddingZone_Domain': area_code,
            'periodStart': start_time.strftime('%Y%m%d%H%M'),
            'periodEnd': end_time.strftime('%Y%m%d%H%M')
        }
        
        logger.info(f"Fetching load data for {country_code} (delay: {data_delay}h) from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        result = _make_entsoe_request(params)
        
        if result.get('status') == 'success':
            result.update({
                'country_code': country_code.upper(),
                'area_code': area_code,
                'data_type': 'electricity_load',
                'time_range': {
                    'start': start_time.strftime('%Y-%m-%d %H:%M'),
                    'end': end_time.strftime('%Y-%m-%d %H:%M'),
                    'hours_requested': hours_back,
                    'data_delay_hours': data_delay
                },
                'document_type': 'A65',
                'process_type': 'A16',
                'note': f'Data delayed by {data_delay} hours due to publication schedule'
            })
        logger.debug(f"Load data for {country_code} results{result}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching electricity load for {country_code}: {e}")
        return {
            'error': f'Failed to retrieve electricity load: {str(e)}',
            'country_code': country_code.upper(),
            'status': 'error'
        }

@tool
def get_electricity_generation(country_code: str, hours_back: int = 6) -> Dict[str, Any]:
    """
    Get electricity generation data for a European country.
    FIXED: Uses proper country-specific data delays and improved error handling.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany, 'FR' for France)
        hours_back: Number of hours of data to fetch (default: 24)
        
    Returns:
        dict: Electricity generation data with timestamps and values in MW
    """
    try:
        # Validate country code
        area_code = _get_area_code(country_code)
        if not area_code:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': _get_supported_countries(),
                'status': 'error'
            }
        

        
        # Get country-specific data delay
        data_delay = 0 # _get_data_delay(country_code)  # Default 36 hours
        
        # Calculate time range with proper delay
        cet = pytz.timezone('Europe/Berlin')
        now_cet = datetime.now(cet)
        
        # Apply country-specific data delay
        end_time = now_cet - timedelta(hours=data_delay)
        start_time = end_time - timedelta(hours=hours_back)
        
        # Round to start of hour for cleaner data
        start_time = start_time.replace(minute=0, second=0, microsecond=0)
        end_time = end_time.replace(minute=0, second=0, microsecond=0)
        
        # Build request parameters
        params = {
            'documentType': ENTSOE_DOCUMENT_TYPES['generation_actual'],  # A75
            'processType': ENTSOE_PROCESS_TYPES['realtime'],             # A16
            'in_Domain': area_code,
            'periodStart': start_time.strftime('%Y%m%d%H%M'),
            'periodEnd': end_time.strftime('%Y%m%d%H%M')
        }
        
        logger.info(f"Fetching generation data for {country_code} (delay: {data_delay}h) from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        result = _make_entsoe_request(params)
        
        if result.get('status') == 'success':
            result.update({
                'country_code': country_code.upper(),
                'area_code': area_code,
                'data_type': 'electricity_generation',
                'time_range': {
                    'start': start_time.strftime('%Y-%m-%d %H:%M'),
                    'end': end_time.strftime('%Y-%m-%d %H:%M'),
                    'hours_requested': hours_back,
                    'data_delay_hours': data_delay
                },
                'document_type': 'A75',
                'process_type': 'A16',
                'note': f'Data delayed by {data_delay} hours due to publication schedule'
            })
        logger.debug(f"Generation  data for {country_code} results{result}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching electricity generation for {country_code}: {e}")
        return {
            'error': f'Failed to retrieve electricity generation: {str(e)}',
            'country_code': country_code.upper(),
            'status': 'error'
        }

@tool
def get_generation_forecast_day_ahead(country_code: str, days_ahead: int = 1) -> Dict[str, Any]:
    """
    Get day-ahead generation forecast for a European country.
    
    This function retrieves the day-ahead generation forecast data from the ENTSOE 
    Transparency Platform. The forecast shows expected electricity generation by 
    production type for today (and optionally additional days).
    
    Note: "Day-ahead" refers to when the forecast was made (yesterday for today's data),
    not the target date. This function retrieves today's generation forecast.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany, 'FR' for France)
        days_ahead: Number of days to fetch forecast data (default: 1, max: 7)
                   1 = today only, 2 = today + tomorrow, etc.
        
    Returns:
        dict: Generation forecast data with the following structure:
            - status: 'success' or 'error'
            - country: Country code
            - data_type: 'generation_forecast_day_ahead'
            - data_points: List of forecast data points with timestamps and values in MW
            - total_points: Number of data points retrieved
            - period_start: Start time of the forecast period (ISO format)
            - period_end: End time of the forecast period (ISO format)
            - timezone_info: Information about timezone handling
            - forecast_horizon: Number of days of forecast data
            
    Example:
        >>> result = get_generation_forecast_day_ahead('DE', 1)
        >>> print(f"Retrieved {result['total_points']} forecast points for Germany")
        >>> for point in result['data_points'][:3]:  # Show first 3 points
        ...     print(f"{point['timestamp']}: {point['value']} MW ({point.get('production_type', 'Total')})")
    """
    try:
        # Validate country code
        area_code = _get_area_code(country_code)
        if not area_code:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': _get_supported_countries(),
                'status': 'error'
            }
        
        # Validate days_ahead parameter
        if not isinstance(days_ahead, int) or days_ahead < 1 or days_ahead > 7:
            return {
                'error': 'days_ahead must be an integer between 1 and 7',
                'status': 'error'
            }
        

        
        # Calculate time range for day-ahead forecast
        # Day-ahead forecasts are typically available for the current day, not future days
        # The "day-ahead" refers to when the forecast was made (the day before), not the target day
        cet_tz = pytz.timezone('Europe/Berlin')
        now_cet = datetime.now(cet_tz)
        
        # For day-ahead forecasts, we get today's data (forecast made yesterday for today)
        # Start from beginning of today in CET
        today = now_cet.date()
        start_time = cet_tz.localize(datetime.combine(today, datetime.min.time()))
        
        # If days_ahead > 1, we can try to get multiple days, but data availability varies
        end_time = start_time + timedelta(days=days_ahead)
        
        # ENTSOE API parameters for generation forecast day-ahead
        # Based on ENTSOE documentation: https://documenter.getpostman.com/view/7009892/2s93JtP3F6#e2e1a56e-2ee1-4b83-b1db-8a3d21cc0ac0
        params = {
            'documentType': ENTSOE_DOCUMENT_TYPES['generation_forecast'],  # A71 - Generation forecast
            'processType': ENTSOE_PROCESS_TYPES['day_ahead'],              # A01 - Day ahead process
            'in_Domain': area_code,                                        # Bidding zone/control area
            'periodStart': start_time.strftime('%Y%m%d%H%M'),              # Start time in ENTSOE format yyyyMMddHHmm
            'periodEnd': end_time.strftime('%Y%m%d%H%M')                   # End time in ENTSOE format yyyyMMddHHmm
        }
        
        # Make the API request
        result = _make_entsoe_request(params)
        
        # Enhance the result with additional metadata
        if result.get('status') == 'success':
            result.update({
                'country': country_code.upper(),
                'data_type': 'generation_forecast_day_ahead',
                'period_start': start_time.isoformat(),
                'period_end': end_time.isoformat(),
                'timezone_info': 'Times in CET/CEST timezone',
                'forecast_horizon': days_ahead,
                'forecast_type': 'Day-ahead generation forecast by production type',
                'data_source': 'ENTSOE Transparency Platform',
                'api_parameters': {
                    'documentType': 'A71 (Generation forecast)',
                    'processType': 'A01 (Day ahead)',
                    'domain': area_code
                }
            })
            
            # Add unit information to data points if available
            for point in result.get('data_points', []):
                if 'unit' not in point:
                    point['unit'] = 'MW'
                # Add forecast context
                point['forecast_type'] = 'day_ahead'
        
        logger.debug(f"Generation forecast day ahead  data for {country_code} results{result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching generation forecast day-ahead for {country_code}: {e}")
        return {
            'error': str(e),
            'country': country_code.upper(),
            'data_type': 'generation_forecast_day_ahead',
            'status': 'error'
        }

@tool
def get_day_ahead_prices(country_code: str, days_back: int = 1) -> Dict[str, Any]:
    """
    Get day-ahead electricity prices for a European country.
    FIXED: Uses country-specific parameter structures and proper delays.
    
    Day-ahead prices have different API parameter requirements by country:
    - Some countries use in_Domain + out_Domain
    - Others use biddingZone_Domain
    - Publication times and delays vary by market coupling participation
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany, 'FR' for France)
        days_back: Number of days back from now to fetch data (default: 1)
        
    Returns:
        dict: Day-ahead electricity prices with timestamps and values in EUR/MWh
    """
    try:
        # Validate country code
        area_code = _get_area_code(country_code)
        if not area_code:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': _get_supported_countries(),
                'status': 'error'
            }
        

        
        # Day-ahead prices have different delays by country
        price_config = {
            'DE': {'delay': 24},  # Germany
            'FR': {'delay': 24},  # France
            'IT': {'delay': 12},  # Italy
            'ES': {'delay': 24},  # Spain
            'NL': {'delay': 24},  # Netherlands
            'BE': {'delay': 24},  # Belgium
            'AT': {'delay': 24},  # Austria
            'CH': {'delay': 24},  # Switzerland
            'PL': {'delay': 24},  # Poland
            'CZ': {'delay': 24},  # Czech Republic
            'DK': {'delay': 24},  # Denmark
            'SE': {'delay': 24},  # Sweden
            'NO': {'delay': 24},  # Norway
            'FI': {'delay': 24},  # Finland
            'GB': {'delay': 24},  # Great Britain
            'IE': {'delay': 24},  # Ireland
            'PT': {'delay': 24}   # Portugal
        }
        
        config = price_config.get(country_code.upper(), {'delay': 24})
        data_delay = config['delay']
        
        # Calculate time range for day-ahead prices
        cet = pytz.timezone('Europe/Berlin')
        now_cet = datetime.now(cet)
        
        # Apply delay and calculate target date
        reference_time = now_cet - timedelta(hours=data_delay)
        target_date = reference_time.date() - timedelta(days=days_back - 1)
        
        # Day-ahead prices are for complete days (00:00 to 24:00)
        start_time = cet.localize(datetime.combine(target_date, datetime.min.time()))
        end_time = start_time + timedelta(days=1)
        
        logger.info(f"Fetching day-ahead prices for {country_code} (delay: {data_delay}h) for date: {target_date.strftime('%Y-%m-%d')}")

        params = {
                'documentType': 'A44',  # Day-ahead prices
                'in_Domain': area_code,
                'out_Domain': area_code,
                'periodStart': start_time.strftime('%Y%m%d%H%M'),
                'periodEnd': end_time.strftime('%Y%m%d%H%M') }

        result = _make_entsoe_request(params)
    
        
        if result.get('status') == 'success':
            # Ensure price units are correct
            for point in result.get('data_points', []):
                if 'unit' in point and 'EUR' not in point['unit']:
                    point['unit'] = 'EUR/MWh'
                elif 'unit' not in point:
                    point['unit'] = 'EUR/MWh'
            
            result.update({
                'country_code': country_code.upper(),
                'area_code': area_code,
                'data_type': 'day_ahead_prices',
                'time_range': {
                    'start': start_time.strftime('%Y-%m-%d %H:%M'),
                    'end': end_time.strftime('%Y-%m-%d %H:%M'),
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'days_requested': days_back,
                    'data_delay_hours': data_delay
                },
                'document_type': 'A44',
                'currency': 'EUR',
                'unit': 'EUR/MWh',
                'note': f'Day-ahead prices for {target_date.strftime("%Y-%m-%d")}. Data delayed by {data_delay} hours.'
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching day-ahead prices for {country_code}: {e}")
        return {
            'error': f'Failed to retrieve day-ahead prices: {str(e)}',
            'country_code': country_code.upper(),
            'status': 'error'
        }

@tool
def get_cross_border_flows(from_country: str, to_country: str, hours_back: int = 24) -> Dict[str, Any]:
    """
    Get cross-border electricity flows between two European countries.
    FIXED: Proper timezone handling, parameter structure, and error handling.
    
    Cross-border flows represent physical electricity flows between interconnected countries.
    Positive values indicate flow from from_country to to_country.
    Negative values indicate flow from to_country to from_country.
    
    Args:
        from_country: Source country code (e.g., 'DE' for Germany)
        to_country: Destination country code (e.g., 'FR' for France)
        hours_back: Number of hours back from now to fetch data (default: 24)
        
    Returns:
        dict: Cross-border flow data with timestamps and values in MW
    """
    try:
        # Validate country codes
        from_area = _get_area_code(from_country)
        to_area = _get_area_code(to_country)
        if not from_area or not to_area:
            return {
                'error': f'Unsupported country code(s): {from_country}, {to_country}',
                'supported_countries': _get_supported_countries(),
                'status': 'error'
            }
        
        # Check if countries are the same
        if from_country.upper() == to_country.upper():
            return {
                'error': 'Cannot get cross-border flows for the same country',
                'status': 'error'
            }
        
        # Use CET timezone like other functions
        cet = pytz.timezone('Europe/Berlin')
        now_cet = datetime.now(cet)
        
        # Cross-border flows typically have minimal delay (15-60 minutes)
        end_time = now_cet - timedelta(hours=1)  # 1 hour delay for safety
        start_time = end_time - timedelta(hours=hours_back)
        
        # Round to hour boundaries for cleaner data
        start_time = start_time.replace(minute=0, second=0, microsecond=0)
        end_time = end_time.replace(minute=0, second=0, microsecond=0)
        
        logger.info(f"Fetching cross-border flows {from_country}->{to_country} from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Try multiple parameter combinations as ENTSOE API can be inconsistent
        param_combinations = [
            {
                'documentType': ENTSOE_DOCUMENT_TYPES['cross_border_flows'],  # A11
                'in_Domain': from_area,                                       # Source area
                'out_Domain': to_area,                                        # Destination area
                'periodStart': start_time.strftime('%Y%m%d%H%M'),
                'periodEnd': end_time.strftime('%Y%m%d%H%M')
            },
        ]
        
        result = None
        last_error = None
        
        for i, params in enumerate(param_combinations):
            logger.debug(f"Trying parameter combination {i+1}/4 for {from_country}->{to_country}")
            result = _make_entsoe_request(params)
            
            if result.get('status') == 'success':
                logger.info(f"Successfully retrieved cross-border flows using method {i+1}")
                
                # If we used the reverse direction (method 4), flip the sign of values
                if i == 3:  # Method 4 (reverse direction)
                    for point in result.get('data_points', []):
                        if point.get('value') is not None:
                            point['value'] = -point['value']
                    result['note'] = 'Data retrieved in reverse direction and values inverted'
                
                break
            else:
                last_error = result.get('error', 'Unknown error')
                logger.debug(f"Method {i+1} failed: {last_error}")
        
        # If all methods failed, return the last error
        if not result or result.get('status') != 'success':
            return {
                'error': f'Failed to retrieve cross-border flows after trying multiple methods. Last error: {last_error}',
                'from_country': from_country.upper(),
                'to_country': to_country.upper(),
                'status': 'error',
                'note': 'Cross-border flow data may not be available for this country pair or time period'
            }
        
        # Enhance successful result with metadata
        result.update({
            'from_country': from_country.upper(),
            'to_country': to_country.upper(),
            'data_type': 'cross_border_flows',
            'time_range': {
                'start': start_time.strftime('%Y-%m-%d %H:%M'),
                'end': end_time.strftime('%Y-%m-%d %H:%M'),
                'hours_requested': hours_back,
                'timezone': 'CET/CEST'
            },
            'flow_direction': f'{from_country.upper()} -> {to_country.upper()}',
            'value_interpretation': 'Positive = export from source to destination, Negative = import to source from destination',
            'unit': 'MW'
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching cross-border flows from {from_country} to {to_country}: {e}")
        return {
            'error': f'Failed to retrieve cross-border flows: {str(e)}',
            'from_country': from_country.upper(),
            'to_country': to_country.upper(),
            'status': 'error'
        }

@tool
def get_renewable_forecast(country_code: str, hours_ahead: int = 48) -> Dict[str, Any]:
    """
    Get wind and solar generation forecast for a European country.
    FIXED: Uses proper timezone handling, data delays, and forecast availability windows.
    
    Renewable forecasts (wind and solar) are typically published with specific schedules:
    - Day-ahead forecasts: Available after market closure (~12:30 CET)
    - Intraday updates: Published throughout the day
    - Forecast horizons: Usually 24-72 hours ahead
    
    Args:
        country_code: Two-letter country code (e.g., 'DE' for Germany, 'FR' for France)
        hours_ahead: Number of hours ahead to fetch forecast data (default: 48, max: 72)
        
    Returns:
        dict: Renewable generation forecast data with timestamps and values in MW
    """
    try:
        # Validate country code
        area_code = _get_area_code(country_code)
        if not area_code:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': _get_supported_countries(),
                'status': 'error'
            }
        

        
        # Limit forecast horizon to reasonable range
        hours_ahead = min(hours_ahead, 72)  # Max 72 hours ahead
        
        # Renewable forecasts have different availability patterns than historical data
        # They're typically available after day-ahead market closure
        forecast_delays = {
            'DE': 6,   # Germany: 6 hours (forecasts available after market closure)
            'FR': 6,   # France: 6 hours
            'IT': 8,   # Italy: 8 hours
            'ES': 6,   # Spain: 6 hours
            'NL': 6,   # Netherlands: 6 hours
            'BE': 6,   # Belgium: 6 hours
            'AT': 6,   # Austria: 6 hours
            'CH': 8,   # Switzerland: 8 hours
            'PL': 8,   # Poland: 8 hours
            'CZ': 6,   # Czech Republic: 6 hours
            'DK': 4,   # Denmark: 4 hours (excellent wind forecasting)
            'SE': 6,   # Sweden: 6 hours
            'NO': 6,   # Norway: 6 hours
            'FI': 6,   # Finland: 6 hours
            'GB': 6,   # Great Britain: 6 hours
            'IE': 6,   # Ireland: 6 hours
            'PT': 6    # Portugal: 6 hours
        }
        
        forecast_delay = forecast_delays.get(country_code.upper(), 6)  # Default 6 hours
        
        # Calculate time range for renewable forecasts
        cet = pytz.timezone('Europe/Berlin')
        now_cet = datetime.now(cet)
        
        # Start from a time when forecasts should be available
        # (current time minus delay to ensure data availability)
        start_time = now_cet - timedelta(hours=forecast_delay)
        end_time = start_time + timedelta(hours=hours_ahead)
        
        # Round to start of hour for cleaner data
        start_time = start_time.replace(minute=0, second=0, microsecond=0)
        end_time = end_time.replace(minute=0, second=0, microsecond=0)
        
        logger.info(f"Fetching renewable forecast for {country_code} (delay: {forecast_delay}h) from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Try multiple parameter combinations for renewable forecasts
        # Forecasts work best with biddingZone_Domain parameter

        params= {
                    'documentType': 'A69',  # Wind and solar forecast
                    'processType': 'A01',   # Day ahead
                    'in_Domain': area_code,
                    'periodStart': start_time.strftime('%Y%m%d%H%M'),
                    'periodEnd': end_time.strftime('%Y%m%d%H%M'),
                }
        
        last_error = None
        
            
        try:
            result = _make_entsoe_request(params)
                
            if result['status'] == 'success':
                # Add renewable-specific metadata
                result.update({
                    'country_code': country_code.upper(),
                    'bidding_zone': area_code,
                    'data_type': 'renewable_forecast',
                    'time_range': {
                        'start': start_time.strftime('%Y-%m-%d %H:%M'),
                        'end': end_time.strftime('%Y-%m-%d %H:%M'),
                        'hours_ahead': hours_ahead,
                        'forecast_delay_hours': forecast_delay
                    },
                    'document_type': params['documentType'],
                    'process_type': 'A01',
                    'forecast_types': ['wind', 'solar'],
                    'note': f'Renewable energy forecast using bidding zone approach'
                })
                
                logger.info(f"Successfully retrieved {result.get('total_points', 0)} renewable forecast points")
                return result
                
            else:
                # Log the error but continue trying other methods
                error_msg = result.get('error', 'Unknown error')
                logger.info(f"Method  failed: {error_msg}")
                last_error = error_msg
                
        except Exception as e:
            logger.info(f"Method exception: {str(e)}")
            last_error = str(e)

        
        # If we get here, all methods failed
        return {
            'error': f'Failed to retrieve renewable forecast: {last_error}. Renewable forecasts may have limited availability or different publication schedules.',
            'country_code': country_code.upper(),
            'area_code': area_code,
            'status': 'error',
            'time_range': {
                'start': start_time.strftime('%Y-%m-%d %H:%M'),
                'end': end_time.strftime('%Y-%m-%d %H:%M'),
                'hours_ahead': hours_ahead,
                'forecast_delay_hours': forecast_delay
            },
            'note': 'Renewable forecasts (A69/A71) have specific publication schedules and may not be available for all countries.',
            'suggestions': [
                'Try a different country (DE, DK, ES are more likely to have renewable forecasts)',
                'Use shorter forecast horizons (24 hours instead of 48+)',
                'Try during European business hours when forecasts are typically updated',
                'Check if the country has significant renewable capacity',
                'Some countries may only provide aggregated generation forecasts'
            ],
            'alternative_functions': [
                'get_generation_forecast_day_ahead() - for total generation forecasts',
                'get_electricity_generation() - for actual renewable generation data',
                'get_day_ahead_prices() - prices often reflect renewable forecast impacts'
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching renewable forecast for {country_code}: {e}")
        return {
            'error': f'Failed to retrieve renewable forecast: {str(e)}',
            'country_code': country_code.upper(),
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
        area_code = _get_area_code(country_code)
        if not area_code:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': _get_supported_countries(),
                'status': 'error'
            }
        

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
        'supported_countries': _get_supported_countries(),
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
        area_code = _get_area_code(country_code)
        if not area_code:
            return {
                'error': f'Unsupported country code: {country_code}',
                'supported_countries': _get_supported_countries(),
                'status': 'error'
            }
        

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


# @tool
# def get_actual_generation_per_unit(country_code: str, date_str: str = None, psr_type: str = None) -> Dict[str, Any]:
#     """
#     Get actual electricity generation per generation unit for a European country.
    
#     This function retrieves detailed generation data showing actual electricity production
#     from individual generation units (power plants) rather than aggregated by fuel type.
#     Uses ENTSOE document type A73 for actual generation.
    
#     IMPORTANT LIMITATIONS (from ENTSOE API):
#     - Maximum time interval: 1 day
#     - Minimum time interval: 1 Market Time Unit
#     - Data typically available for historical periods (not real-time)
#     - Uses A73 (Actual generation) with A16 (Realised) process type
    
#     Based on ENTSOE API documentation with correct parameters:
#     - documentType: A73 (Actual generation)
#     - processType: A16 (Realised)
#     - in_Domain: EIC code of Control Area
    
#     Args:
#         country_code: Two-letter country code (e.g., 'BE' for Belgium, 'DE' for Germany)
#         date_str: Date string in format 'YYYY-MM-DD' (e.g., '2023-08-15'). 
#                  If None, tries yesterday. Historical dates work better.
#         psr_type: Optional production source type filter (e.g., 'B14' for Nuclear, 'B16' for Solar)
#                  Available types: B01=Biomass, B02=Brown coal, B04=Gas, B05=Hard coal, 
#                  B06=Oil, B09=Geothermal, B10=Hydro Pumped, B11=Hydro Run-of-river,
#                  B12=Hydro Reservoir, B14=Nuclear, B15=Other renewable, B16=Solar,
#                  B17=Waste, B18=Wind Offshore, B19=Wind Onshore, B20=Other
        
#     Returns:
#         dict: Generation data with the following structure:
#             - status: 'success' or 'error'
#             - data_points: List of generation data points per unit
#             - total_points: Number of data points retrieved
#             - country_code: Country code used
#             - time_range: Start and end times for the data
#             - units: List of generation units found
#             - psr_type_filter: Production source type filter applied (if any)
#             - error: Error message (if status is 'error')
            
#     Example:
#         >>> # Get historical data (works better)
#         >>> result = get_actual_generation_per_unit('BE', '2023-08-15')
#         >>> if result['status'] == 'success':
#         ...     print(f"Found {result['total_points']} data points")
        
#         >>> # Get only nuclear generation for a specific date
#         >>> result = get_actual_generation_per_unit('BE', '2023-08-15', psr_type='B14')
        
#         >>> # Try recent data (may not be available)
#         >>> result = get_actual_generation_per_unit('BE')  # Uses yesterday
#     """
#     try:
#         # Validate country code
#         area_code = _get_area_code(country_code)
#         if not area_code:
#             return {
#                 'error': f'Unsupported country code: {country_code}. Supported countries: {_get_supported_countries()}',
#                 'status': 'error'
#             }
        
#         # Calculate time range
#         cet_tz = pytz.timezone('Europe/Berlin')
        
#         if date_str:
#             # Parse provided date
#             print(date_str)
#             try:
#                 target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
#                 start_time = cet_tz.localize(datetime.combine(target_date, datetime.min.time().replace(hour=22)))
#                 end_time = start_time + timedelta(hours=6)
#             except ValueError:
#                 return {
#                     'error': f'Invalid date format: {date_str}. Use YYYY-MM-DD format (e.g., 2023-08-15)',
#                     'status': 'error'
#                 }
#         else:
#             # Use yesterday (most likely to have data)
#             now_cet = datetime.now(cet_tz)
#             yesterday = now_cet.date() - timedelta(days=1)
#             start_time = cet_tz.localize(datetime.combine(yesterday, datetime.min.time().replace(hour=22)))
#             end_time = start_time + timedelta(hours=6)
#             print(end_time)
        
#         # Build parameters for actual generation (A73)
#         params = {
#             'documentType': 'A73',                                                # A73 = Actual generation
#             'processType': 'A16',                                                 # A16 = Realised
#             'in_Domain': area_code,                                               # EIC code of Control Area
#             'periodStart': start_time.strftime('%Y%m%d%H%M'),                     # Pattern yyyyMMddHHmm
#             'periodEnd': end_time.strftime('%Y%m%d%H%M')                          # Pattern yyyyMMddHHmm
#         }
        
#         # Add optional PsrType filter if specified
#         if psr_type:
#             params['PsrType'] = psr_type
        
#         logger.info(f"Requesting actual generation for {country_code} from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
#         if psr_type:
#             logger.info(f"Filtering by production source type: {psr_type}")
        
#         # Make the API request
#         result = _make_entsoe_request(params)
        
#         if result['status'] == 'success':
#             # Parse the response and extract unit information
#             parsed_data = result.copy()
            
#             # Extract unique generation units from the data
#             units = set()
#             production_types = set()
            
#             if 'data_points' in parsed_data:
#                 for point in parsed_data['data_points']:
#                     # Try different possible field names for unit identification
#                     unit_name = None
#                     if 'unit_name' in point:
#                         unit_name = point['unit_name']
#                     elif 'resource_name' in point:
#                         unit_name = point['resource_name']
#                     elif 'registered_resource' in point.get('metadata', {}):
#                         unit_name = point['metadata']['registered_resource']
#                     elif 'mRID' in point:
#                         unit_name = point['mRID']
#                     elif 'production_type' in point:
#                         # Use production type as identifier if no unit name available
#                         unit_name = f"Unit_{point['production_type']}"
                    
#                     if unit_name:
#                         units.add(unit_name)
                    
#                     # Track production types
#                     if 'production_type' in point:
#                         production_types.add(point['production_type'])
            
#             # Add additional metadata
#             parsed_data.update({
#                 'country_code': country_code.upper(),
#                 'time_range': {
#                     'start': start_time.strftime('%Y-%m-%d %H:%M'),
#                     'end': end_time.strftime('%Y-%m-%d %H:%M'),
#                     'date_requested': date_str or 'yesterday',
#                     'interval': '1 day (API maximum)'
#                 },
#                 'units': list(units),
#                 'production_types': list(production_types),
#                 'psr_type_filter': psr_type,
#                 'data_type': 'actual_generation_per_unit',
#                 'document_type': 'A73 (Actual generation)',
#                 'process_type': 'A16 (Realised)',
#                 'api_endpoint': 'ENTSOE Transparency Platform',
#                 'api_limitations': {
#                     'max_interval': '1 day',
#                     'min_interval': '1 Market Time Unit',
#                     'note': 'Historical data typically more available than real-time'
#                 },
#                 'note': 'Data shows actual generation from individual power plants/units'
#             })
            
#             logger.info(f"Successfully retrieved {parsed_data.get('total_points', 0)} data points for {len(units)} generation units")
#             return parsed_data
#         else:
#             # Enhance error message with helpful guidance
#             error_msg = result.get('error', 'Unknown error')
#             if 'No matching data found' in error_msg:
#                 enhanced_error = f"{error_msg}\n\nTip: Try historical dates (e.g., '2023-08-15') as recent data may not be available for detailed generation per unit."
#                 result['error'] = enhanced_error
            
#             logger.error(f"Failed to retrieve actual generation data: {result.get('error')}")
#             return result
            
#     except Exception as e:
#         logger.error(f"Error getting actual generation for {country_code}: {e}")
#         return {
#             'error': f'Failed to retrieve actual generation data: {str(e)}',
#             'country_code': country_code.upper(),
#             'status': 'error'
#         }

@tool
def get_unavailability_production_units(country_code: str, days_back: int = 7) -> Dict[str, Any]:
    """
    Get unavailability information for electricity production units (power plants) in a European country.
    
    ⚠️  **IMPORTANT DATA AVAILABILITY WARNING** ⚠️
    This function accesses ENTSOE document type A77 (Unavailability of Generation Units), which has 
    EXTREMELY LIMITED availability. Most European TSOs do NOT provide this data publicly, and many 
    restrict it to registered market participants only. Expect frequent "No data found" responses.
    
    **Alternative Recommendations:**
    - Use get_electricity_generation() for actual generation data
    - Use get_generation_forecast_day_ahead() for planned generation
    - Use get_renewable_forecast() for renewable generation forecasts
    
    This function retrieves data about planned and unplanned outages of generation units,
    including maintenance schedules and forced outages that affect electricity production capacity.
    
    Args:
        country_code: Two-letter country code (e.g., 'BE' for Belgium, 'DE' for Germany)
        days_back: Number of days of historical unavailability data to retrieve (default: 7, max: 30)
        
    Returns:
        dict: Unavailability data with the following structure:
            - status: 'success' or 'error' (expect 'error' most of the time)
            - data_points: List of unavailability events (usually empty)
            - total_points: Number of unavailability events retrieved
            - country_code: Country code used
            - time_range: Start and end times for the data
            - unavailability_types: Types of unavailabilities found (planned, unplanned, etc.)
            - affected_units: List of generation units with unavailabilities
            - error: Error message (if status is 'error')
            - suggestions: List of alternative approaches if data is not available
            
    Example:
        >>> result = get_unavailability_production_units('BE', 7)
        >>> if result['status'] == 'success':
        ...     print(f"Found {result['total_points']} unavailability events")
        ...     print(f"Affected units: {len(result.get('affected_units', []))}")
        >>> else:
        ...     print(f"No data available: {result['error']}")
        ...     print("Consider using alternative functions:", result.get('alternative_functions', []))
    """
    try:
        # Validate country code
        area_code = _get_area_code(country_code)
        if not area_code:
            return {
                'error': f'Unsupported country code: {country_code}. Supported countries: {_get_supported_countries()}',
                'status': 'error'
            }
        

        
        # Limit days_back to reasonable range (unavailability data has limited availability)
        days_back = min(days_back, 30)  # Max 30 days
        
        # Get country-specific data delay (unavailability data typically has longer delays)
        data_delay = _get_data_delay(country_code)
        # Add extra delay for unavailability data (typically published later)
        data_delay += 24  # Additional 24 hours for unavailability data
        
        # Calculate time range with proper delay
        cet = pytz.timezone('Europe/Berlin')
        now_cet = datetime.now(cet)
        
        # Apply data delay and go back the requested days
        end_time = now_cet - timedelta(hours=data_delay)
        start_time = end_time - timedelta(days=days_back)
        
        # Round to start/end of day for unavailability data (daily granularity)
        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = end_time.replace(hour=23, minute=59, second=0, microsecond=0)
        
        logger.info(f"Requesting unavailability data for {country_code} (delay: {data_delay}h) from {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
        
        # Try multiple parameter combinations based on ENTSOE API documentation
        # The unavailability API (A77) has very specific parameter requirements and limited availability
        param_combinations = [
            {
                'documentType': ENTSOE_DOCUMENT_TYPES['unavailability_generation'],  # A77
                'biddingZone_Domain': area_code,
                'periodStart': start_time.strftime('%Y%m%d%H%M'),
                'periodEnd': end_time.strftime('%Y%m%d%H%M')
            }
        ]
        
        last_error = None
        
        for i, params in enumerate(param_combinations):
            logger.debug(f"Trying unavailability parameter combination {i+1}/{len(param_combinations)} for {country_code}")
            
            try:
                result = _make_entsoe_request(params)
                
                if result.get('status') == 'success':
                    logger.info(f"Successfully retrieved unavailability data using method {i+1}")
                    
                    # Parse the response and extract unavailability information
                    parsed_data = result.copy()
                    
                    # Extract unavailability types and affected units from the data
                    unavailability_types = set()
                    affected_units = set()
                    
                    if 'data_points' in parsed_data:
                        for point in parsed_data['data_points']:
                            # Extract unavailability type if available
                            if 'unavailability_type' in point:
                                unavailability_types.add(point['unavailability_type'])
                            elif 'business_type' in point.get('metadata', {}):
                                unavailability_types.add(point['metadata']['business_type'])
                            
                            # Extract affected unit information
                            if 'unit_name' in point:
                                affected_units.add(point['unit_name'])
                            elif 'resource_name' in point:
                                affected_units.add(point['resource_name'])
                            elif 'registered_resource' in point.get('metadata', {}):
                                affected_units.add(point['metadata']['registered_resource'])
                    
                    # Add additional metadata
                    parsed_data.update({
                        'country_code': country_code.upper(),
                        'area_code': area_code,
                        'time_range': {
                            'start': start_time.strftime('%Y-%m-%d %H:%M'),
                            'end': end_time.strftime('%Y-%m-%d %H:%M'),
                            'days_requested': days_back,
                            'data_delay_hours': data_delay
                        },
                        'unavailability_types': list(unavailability_types),
                        'affected_units': list(affected_units),
                        'data_type': 'unavailability_production_units',
                        'document_type': 'A77',
                        'api_endpoint': 'ENTSOE Transparency Platform',
                        'note': f'Includes both planned maintenance and unplanned outages. Data delayed by {data_delay} hours.',
                        'method_used': f'Parameter combination {i+1}'
                    })
                    
                    logger.info(f"Successfully retrieved {parsed_data.get('total_points', 0)} unavailability events for {len(affected_units)} units")
                    return parsed_data
                
                else:
                    # Log the error but continue trying other methods
                    error_msg = result.get('error', 'Unknown error')
                    logger.debug(f"Method {i+1} failed: {error_msg}")
                    last_error = error_msg
                    
            except Exception as e:
                logger.debug(f"Method {i+1} exception: {str(e)}")
                last_error = str(e)
    
        # If we get here, all methods failed
        # Provide specific guidance based on the type of error
        error_analysis = "Unknown error"
        specific_suggestions = []
        
        if last_error:
            if "No matching data found" in last_error:
                error_analysis = "No unavailability data available for the requested period"
                specific_suggestions = [
                    f"{country_code} TSO may not publish unavailability data publicly",
                    "Try a different time period (some countries only report during maintenance seasons)",
                    "Try a different country (DE, FR, NL often have better data availability)",
                    "This data type may require market participant registration"
                ]
            elif "XML parsing" in last_error or "not well-formed" in last_error:
                error_analysis = "API returned invalid XML response (likely HTML error page)"
                specific_suggestions = [
                    "The ENTSOE API may be returning an error page instead of XML",
                    "Try again later - the API may be temporarily unavailable",
                    "Check if your API token has access to unavailability data",
                    "Some countries restrict this data to registered market participants"
                ]
            elif "Bad Request" in last_error:
                error_analysis = "Invalid API parameters for unavailability data"
                specific_suggestions = [
                    "The country may not support unavailability data queries",
                    "Try different time periods or parameters",
                    "Check ENTSOE documentation for country-specific requirements"
                ]
        
        return {
            'error': f'Failed to retrieve unavailability data after trying {len(param_combinations)} methods. Last error: {last_error}',
            'error_analysis': error_analysis,
            'country_code': country_code.upper(),
            'area_code': area_code,
            'status': 'error',
            'time_range': {
                'start': start_time.strftime('%Y-%m-%d %H:%M'),
                'end': end_time.strftime('%Y-%m-%d %H:%M'),
                'days_requested': days_back,
                'data_delay_hours': data_delay
            },
            'data_availability_note': 'Unavailability data (A77) has extremely limited availability. Most TSOs do not provide this data publicly.',
            'suggestions': specific_suggestions + [
                'Consider using alternative data types for generation analysis',
                'Try get_electricity_generation() for actual generation data',
                'Try get_generation_forecast_day_ahead() for planned generation',
                'Contact the TSO directly for unavailability information'
            ],
            'countries_with_better_availability': ['DE', 'FR', 'NL', 'BE'],
            'alternative_functions': [
                'get_electricity_generation() - actual generation by type',
                'get_electricity_load() - consumption data',
                'get_generation_forecast_day_ahead() - planned generation',
                'get_renewable_forecast() - renewable generation forecasts'
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting unavailability data for {country_code}: {e}")
        return {
            'error': f'Failed to retrieve unavailability data: {str(e)}',
            'country_code': country_code.upper(),
            'status': 'error'
        }
