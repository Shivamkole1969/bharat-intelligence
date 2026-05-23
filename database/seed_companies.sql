-- ============================================================
-- Bharat Market Intelligence Agent — Seed Companies
-- Top 50 Indian companies across key sectors for MVP demo
-- ============================================================

INSERT INTO companies (symbol, exchange, isin, company_name, sector, industry, nse_symbol, bse_code, is_active)
VALUES
    -- IT Services
    ('TCS', 'NSE', 'INE467B01029', 'Tata Consultancy Services Ltd', 'Information Technology', 'IT Services', 'TCS', '532540', TRUE),
    ('INFY', 'NSE', 'INE009A01021', 'Infosys Ltd', 'Information Technology', 'IT Services', 'INFY', '500209', TRUE),
    ('WIPRO', 'NSE', 'INE075A01022', 'Wipro Ltd', 'Information Technology', 'IT Services', 'WIPRO', '507685', TRUE),
    ('HCLTECH', 'NSE', 'INE860A01027', 'HCL Technologies Ltd', 'Information Technology', 'IT Services', 'HCLTECH', '532281', TRUE),
    ('TECHM', 'NSE', 'INE669C01036', 'Tech Mahindra Ltd', 'Information Technology', 'IT Services', 'TECHM', '532755', TRUE),
    ('LTIM', 'NSE', 'INE214T01019', 'LTIMindtree Ltd', 'Information Technology', 'IT Services', 'LTIM', '540005', TRUE),

    -- Banking
    ('HDFCBANK', 'NSE', 'INE040A01034', 'HDFC Bank Ltd', 'Financial Services', 'Banking', 'HDFCBANK', '500180', TRUE),
    ('ICICIBANK', 'NSE', 'INE090A01021', 'ICICI Bank Ltd', 'Financial Services', 'Banking', 'ICICIBANK', '532174', TRUE),
    ('SBIN', 'NSE', 'INE062A01020', 'State Bank of India', 'Financial Services', 'Banking', 'SBIN', '500112', TRUE),
    ('KOTAKBANK', 'NSE', 'INE237A01028', 'Kotak Mahindra Bank Ltd', 'Financial Services', 'Banking', 'KOTAKBANK', '500247', TRUE),
    ('AXISBANK', 'NSE', 'INE238A01034', 'Axis Bank Ltd', 'Financial Services', 'Banking', 'AXISBANK', '532215', TRUE),
    ('INDUSINDBK', 'NSE', 'INE095A01012', 'IndusInd Bank Ltd', 'Financial Services', 'Banking', 'INDUSINDBK', '532187', TRUE),

    -- Oil & Gas / Energy
    ('RELIANCE', 'NSE', 'INE002A01018', 'Reliance Industries Ltd', 'Energy', 'Oil & Gas', 'RELIANCE', '500325', TRUE),
    ('ONGC', 'NSE', 'INE213A01029', 'Oil and Natural Gas Corporation Ltd', 'Energy', 'Oil & Gas', 'ONGC', '500312', TRUE),
    ('BPCL', 'NSE', 'INE029A01011', 'Bharat Petroleum Corporation Ltd', 'Energy', 'Oil & Gas', 'BPCL', '500547', TRUE),
    ('IOC', 'NSE', 'INE242A01010', 'Indian Oil Corporation Ltd', 'Energy', 'Oil & Gas', 'IOC', '530965', TRUE),
    ('NTPC', 'NSE', 'INE733E01010', 'NTPC Ltd', 'Energy', 'Power', 'NTPC', '532555', TRUE),
    ('POWERGRID', 'NSE', 'INE752E01010', 'Power Grid Corporation of India Ltd', 'Energy', 'Power', 'POWERGRID', '532898', TRUE),
    ('ADANIENT', 'NSE', 'INE423A01024', 'Adani Enterprises Ltd', 'Energy', 'Conglomerate', 'ADANIENT', '512599', TRUE),
    ('ADANIGREEN', 'NSE', 'INE364U01010', 'Adani Green Energy Ltd', 'Energy', 'Renewable Energy', 'ADANIGREEN', '541450', TRUE),

    -- Automobile
    ('TATAMOTORS', 'NSE', 'INE155A01022', 'Tata Motors Ltd', 'Automobile', 'Auto - Passenger', 'TATAMOTORS', '500570', TRUE),
    ('MARUTI', 'NSE', 'INE585B01010', 'Maruti Suzuki India Ltd', 'Automobile', 'Auto - Passenger', 'MARUTI', '532500', TRUE),
    ('M&M', 'NSE', 'INE101A01026', 'Mahindra & Mahindra Ltd', 'Automobile', 'Auto - Passenger', 'M&M', '500520', TRUE),
    ('BAJAJ-AUTO', 'NSE', 'INE917I01010', 'Bajaj Auto Ltd', 'Automobile', 'Auto - Two Wheeler', 'BAJAJ-AUTO', '532977', TRUE),
    ('EICHERMOT', 'NSE', 'INE066A01021', 'Eicher Motors Ltd', 'Automobile', 'Auto - Two Wheeler', 'EICHERMOT', '505200', TRUE),

    -- Pharma & Healthcare
    ('SUNPHARMA', 'NSE', 'INE044A01036', 'Sun Pharmaceutical Industries Ltd', 'Healthcare', 'Pharmaceuticals', 'SUNPHARMA', '524715', TRUE),
    ('DRREDDY', 'NSE', 'INE089A01023', 'Dr. Reddys Laboratories Ltd', 'Healthcare', 'Pharmaceuticals', 'DRREDDY', '500124', TRUE),
    ('CIPLA', 'NSE', 'INE059A01026', 'Cipla Ltd', 'Healthcare', 'Pharmaceuticals', 'CIPLA', '500087', TRUE),
    ('APOLLOHOSP', 'NSE', 'INE437A01024', 'Apollo Hospitals Enterprise Ltd', 'Healthcare', 'Hospitals', 'APOLLOHOSP', '508869', TRUE),
    ('DIVISLAB', 'NSE', 'INE361B01024', 'Divis Laboratories Ltd', 'Healthcare', 'Pharmaceuticals', 'DIVISLAB', '532488', TRUE),

    -- FMCG
    ('HINDUNILVR', 'NSE', 'INE030A01027', 'Hindustan Unilever Ltd', 'FMCG', 'FMCG', 'HINDUNILVR', '500696', TRUE),
    ('ITC', 'NSE', 'INE154A01025', 'ITC Ltd', 'FMCG', 'FMCG', 'ITC', '500875', TRUE),
    ('NESTLEIND', 'NSE', 'INE239A01016', 'Nestle India Ltd', 'FMCG', 'FMCG', 'NESTLEIND', '500790', TRUE),
    ('BRITANNIA', 'NSE', 'INE216A01030', 'Britannia Industries Ltd', 'FMCG', 'FMCG', 'BRITANNIA', '500825', TRUE),
    ('TATACONSUM', 'NSE', 'INE192A01025', 'Tata Consumer Products Ltd', 'FMCG', 'FMCG', 'TATACONSUM', '500800', TRUE),

    -- Metals & Mining
    ('TATASTEEL', 'NSE', 'INE081A01020', 'Tata Steel Ltd', 'Metals & Mining', 'Steel', 'TATASTEEL', '500470', TRUE),
    ('JSWSTEEL', 'NSE', 'INE019A01038', 'JSW Steel Ltd', 'Metals & Mining', 'Steel', 'JSWSTEEL', '500228', TRUE),
    ('HINDALCO', 'NSE', 'INE038A01020', 'Hindalco Industries Ltd', 'Metals & Mining', 'Aluminium', 'HINDALCO', '500440', TRUE),
    ('COALINDIA', 'NSE', 'INE522F01014', 'Coal India Ltd', 'Metals & Mining', 'Coal', 'COALINDIA', '533278', TRUE),

    -- Financial Services (Non-Banking)
    ('BAJFINANCE', 'NSE', 'INE296A01024', 'Bajaj Finance Ltd', 'Financial Services', 'NBFC', 'BAJFINANCE', '500034', TRUE),
    ('BAJAJFINSV', 'NSE', 'INE918I01018', 'Bajaj Finserv Ltd', 'Financial Services', 'Financial Holding', 'BAJAJFINSV', '532978', TRUE),
    ('HDFCLIFE', 'NSE', 'INE795G01014', 'HDFC Life Insurance Company Ltd', 'Financial Services', 'Insurance', 'HDFCLIFE', '540777', TRUE),
    ('SBILIFE', 'NSE', 'INE123W01016', 'SBI Life Insurance Company Ltd', 'Financial Services', 'Insurance', 'SBILIFE', '540719', TRUE),

    -- Cement & Construction
    ('ULTRACEMCO', 'NSE', 'INE481G01011', 'UltraTech Cement Ltd', 'Construction', 'Cement', 'ULTRACEMCO', '532538', TRUE),
    ('GRASIM', 'NSE', 'INE047A01021', 'Grasim Industries Ltd', 'Construction', 'Cement & Textiles', 'GRASIM', '500300', TRUE),
    ('LT', 'NSE', 'INE018A01030', 'Larsen & Toubro Ltd', 'Construction', 'Engineering', 'LT', '500510', TRUE),

    -- Telecom
    ('BHARTIARTL', 'NSE', 'INE397D01024', 'Bharti Airtel Ltd', 'Telecom', 'Telecom', 'BHARTIARTL', '532454', TRUE),

    -- Consumer Durables
    ('TITAN', 'NSE', 'INE280A01028', 'Titan Company Ltd', 'Consumer Durables', 'Jewellery & Watches', 'TITAN', '500114', TRUE),
    ('ASIANPAINT', 'NSE', 'INE021A01026', 'Asian Paints Ltd', 'Consumer Durables', 'Paints', 'ASIANPAINT', '500820', TRUE),

    -- Chemicals
    ('PIDILITIND', 'NSE', 'INE318A01026', 'Pidilite Industries Ltd', 'Chemicals', 'Specialty Chemicals', 'PIDILITIND', '500331', TRUE)

ON CONFLICT (exchange, symbol) DO NOTHING;

-- Seed data sources
INSERT INTO data_sources (source_name, source_type, base_url, reliability_score, license_notes, is_active)
VALUES
    ('BSE India', 'exchange', 'https://www.bseindia.com', 0.95, 'Public corporate announcements via BSE website', TRUE),
    ('NSE India', 'exchange', 'https://www.nseindia.com', 0.95, 'Public corporate announcements via NSE website', TRUE),
    ('MoneyControl', 'news', 'https://www.moneycontrol.com', 0.80, 'Public financial news aggregator', TRUE),
    ('Economic Times', 'news', 'https://economictimes.indiatimes.com', 0.80, 'Public financial news', TRUE),
    ('LiveMint', 'news', 'https://www.livemint.com', 0.80, 'Public financial news', TRUE),
    ('RBI', 'regulator', 'https://www.rbi.org.in', 0.98, 'Reserve Bank of India public releases', TRUE),
    ('SEBI', 'regulator', 'https://www.sebi.gov.in', 0.98, 'Securities and Exchange Board of India circulars', TRUE),
    ('Yahoo Finance', 'market_data', 'https://finance.yahoo.com', 0.70, 'Delayed market data for educational/demo use only via yfinance', TRUE),
    ('Company IR Pages', 'company', NULL, 0.90, 'Investor relations pages of individual companies', TRUE),
    ('Earnings Transcripts', 'transcript', NULL, 0.85, 'Public earnings call transcripts', TRUE)
ON CONFLICT DO NOTHING;
