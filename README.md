# JobNet.az Candidate Scraper

High-performance web scraper for extracting candidate data from JobNet.az API with contact information.

## Features

- ¡ **Async/Await Optimization**: Uses `aiohttp` and `asyncio` for concurrent requests
- =€ **High Performance**: 10-15x faster than synchronous version
- =Ê **Dual Output**: Saves data in both JSON and CSV formats
- = **Rate Limiting**: Configurable request delays and concurrency limits
- =Þ **Contact Data**: Extracts email, phone, address, and personal details
- =á **Error Handling**: Robust retry logic with exponential backoff
- =Ý **Detailed Logging**: Complete logging with separate log files
- ø **Graceful Interruption**: Can be stopped with Ctrl+C and saves partial data

## Installation

1. **Clone or download the files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Start
```bash
# Run the optimized async version (recommended)
python3 jobnet_scraper_async.py

# Or run the basic synchronous version
python3 jobnet_scraper.py
```

### Configuration

Edit the configuration in `jobnet_scraper_async.py`:
```python
max_concurrent = 15      # Number of concurrent requests (adjust based on API limits)
request_delay = 0.05     # Delay between requests in seconds (50ms)
```

## Performance Comparison

| Version | Speed | Concurrent Requests | Estimated Time |
|---------|--------|-------------------|---------------|
| Sync    | ~2 candidates/sec | 1 | ~4 minutes |
| Async   | ~20-30 candidates/sec | 15 | ~30-45 seconds |

## Output Files

The scraper generates timestamped files:
- `jobnet_candidates_async_YYYYMMDD_HHMMSS.json` - Complete structured data
- `jobnet_candidates_async_YYYYMMDD_HHMMSS.csv` - Tabular data for spreadsheets
- `scraper_async.log` - Detailed execution logs

## Data Extracted

### Contact Information
- Email address
- Phone number  
- Physical address
- Date of birth

### Professional Information
- Position/Job title
- Salary expectations
- Work experience history
- Skills and competencies
- Language proficiencies
- Education background
- Certificates
- Driver licenses

### Profile Information
- Name and personal details
- Location (city)
- Job category
- Profile image
- Account status (premium/sponsored)
- View statistics

## API Structure

The scraper works with two main endpoints:
1. **Listings API**: `https://api.jobnet.az/api/v1/job-seekers?page={page}`
   - Returns paginated list of candidates with basic info
   - Extracts `slug` for each candidate

2. **Detail API**: `https://api.jobnet.az/api/v1/job-seekers/{slug}`
   - Returns complete candidate profile including contact information
   - Example: `https://api.jobnet.az/api/v1/job-seekers/ilkin-xxx-6480`

## Error Handling

- **Rate Limiting**: Automatic retry with exponential backoff for 429 responses
- **Network Errors**: Configurable retry attempts with delays
- **Partial Data**: Saves successfully scraped data even if interrupted
- **Failed Candidates**: Logs and tracks candidates that couldn't be processed

## Logging

Detailed logs include:
- Request/response timing
- Failed candidate tracking
- Processing statistics
- Error messages with context

## Respect for API

The scraper includes several measures to be respectful to the JobNet API:
- Configurable rate limiting
- Reasonable concurrent request limits
- Proper error handling
- Request delays between batches
- Browser-like headers

## Troubleshooting

### Common Issues

1. **Rate Limiting (429 errors)**
   - Increase `request_delay` (e.g., 0.1 or 0.2)
   - Decrease `max_concurrent_requests` (e.g., 5-10)

2. **Connection Timeouts**
   - Check internet connection
   - Increase timeout values in the code

3. **Memory Issues**
   - Reduce `batch_size` in processing logic
   - Process in smaller chunks

### Performance Tuning

- **Fast Connection**: `max_concurrent=20`, `request_delay=0.02`
- **Stable Connection**: `max_concurrent=15`, `request_delay=0.05` (default)
- **Slow/Unstable**: `max_concurrent=5`, `request_delay=0.1`

## Dependencies

- `aiohttp==3.9.5` - Async HTTP client
- `aiofiles==24.1.0` - Async file I/O
- `requests==2.31.0` - HTTP library (for sync version)

## Legal Notice

This tool is for educational and research purposes. Please:
- Respect the website's terms of service
- Use reasonable request rates
- Don't overload the server
- Consider reaching out to JobNet for official API access for commercial use

## License

This project is provided as-is for educational purposes.