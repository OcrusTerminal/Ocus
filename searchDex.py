import requests
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Set
import time 
import re
from difflib import SequenceMatcher

class ImprovedTokenSearcher:
    def __init__(self):
        self.dexscreener_base_url = "https://api.dexscreener.com/latest/dex"
        # Expanded stop words to catch more common terms
        self.stop_words = {
            'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'but', 'by', 'from',
            'that', 'this', 'these', 'those', 'what', 'which', 'who', 'whom',
            'whose', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
            'im', 'its', 'it', 'like', 'oh', 'no', 'yes', 'not', 'about',
            'again', 'just', 'dont', 'she', 'he', 'we', 'they', 'you', 'your',
            
            'because', 'since', 'as', 'until', 'while', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'up', 'down', 'out', 'on', 'off', 'over', 'under',
            
            'touch', 'touched', 'touching', 'talk', 'talked', 'talking',
            'say', 'said', 'saying', 'look', 'looked', 'looking',
            'get', 'got', 'getting', 'go', 'going', 'gone',
            
            'lol', 'omg', 'wtf', 'tbh', 'af', 'rn', 'gonna', 'wanna',
            'doesnt', 'dont', 'cant', 'wont', 'shouldnt', 'wouldnt',
            
            'i', 'me', 'my', 'mine', 'you', 'your', 'yours', 'he', 'him',
            'his', 'she', 'her', 'hers', 'it', 'its', 'we', 'us', 'our',
            'ours', 'they', 'them', 'their', 'theirs'
        }
        
        self.spam_indicators = {
            'common_suffixes': {'inu', 'elon', 'safe', 'moon', 'gem', 'doge', 'shib'},
            'generic_prefixes': {'baby', 'mini', 'lite', 'super'},
            'marketing_terms': {'rewards', 'presale', 'fair', 'launch'},
            'trend_riders': {'ai', 'chad', 'based', 'wojak', 'pepe'},
            'suspicious_patterns': [
                r'\d{3,}',
                r'[A-Z]{5,}',
                r'v[0-9]',
                r'[0-9]x',
                r'[A-Z][a-z]+[A-Z]',
                r'[!@#$%^&*()_+=\[\]{};:"|<>?]'
            ]
        }
        self.min_requirements = {
            'liquidity_usd': 5000,   
            'volume_24h': 500,       
            'price_usd': 0.000000001, 
            'market_cap': 200000    

        }
        
       
        # Add market cap to market weights
        self.market_weights = {
            'liquidity': {
                'weight': 2.0,
                'thresholds': [5000, 25000, 50000, 100000]
            },
            'volume': {
                'weight': 1.5,
                'thresholds': [500, 5000, 25000, 50000]
            },
            'market_cap': {
                'weight': 1.8,
                'thresholds': [100000, 1000000, 10000000]
            }
        }
        
        
        self.debug_mode = True

        self.term_weights = {
            'name_exact': 3.0,
            'name_partial': 2.0,
            'tag_exact': 1.5,
            'tag_partial': 1.0,
            'context_bonus': 0.5,
        }

    def extract_meaningful_phrases(self, text: str) -> List[Tuple[str, float]]:
        """Extract meaningful phrases while avoiding common terms"""
        if not text:
            return []

        # Normalize text
        text = self.normalize_text(text)
        
        # Split into words and remove stop words
        words = [w for w in text.split() if w not in self.stop_words and len(w) > 2]
        
        if not words:
            return []
            
        phrases = []
        
        for word in words:
            if (len(word) > 4) or (word[0].isupper() and len(word) > 3):
                phrases.append((word, self.term_weights['name_partial']))
        
        for i in range(len(words) - 1):
            if len(words[i]) > 2 and len(words[i+1]) > 2:  # Both words must be substantial
                phrase = f"{words[i]} {words[i+1]}"
                # Higher weight for proper noun combinations
                if words[i][0].isupper() or words[i+1][0].isupper():
                    phrases.append((phrase, self.term_weights['name_exact']))
                else:
                    phrases.append((phrase, self.term_weights['name_partial']))
        
        if len(words) >= 3:
            for i in range(len(words) - 2):
                if any(word[0].isupper() for word in words[i:i+3]):
                    phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                    phrases.append((phrase, self.term_weights['name_exact'] + 0.5))
        
        return phrases

    def normalize_text(self, text: str) -> str:
        """Normalize text while preserving meaningful capitalization"""
        if not text:
            return ""
        # Remove special characters but preserve spaces and capitalization
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    def extract_searchable_terms(self, meme_entry: Dict) -> List[Tuple[str, float]]:
        """Extract terms with improved filtering"""
        terms = {}
        
        # Process name
        if name := meme_entry.get('name'):
            print(f"\nProcessing meme: {name}")
            phrases = self.extract_meaningful_phrases(name)
            
            for phrase, weight in phrases:
                if len(phrase.split()) <= 3 and not self.is_spam_term(phrase):  # Limit phrase length
                    terms[phrase] = max(terms.get(phrase, 0), weight)
        
        # Process tags, giving preference to proper nouns and specific terms
        for tag_list in [meme_entry.get('tags', []), meme_entry.get('list_tags', [])]:
            for tag in tag_list:
                if not tag:
                    continue
                
                # Only process tags that might contain meaningful terms
                if any(word[0].isupper() for word in tag.split()) or len(tag.split()) <= 2:
                    phrases = self.extract_meaningful_phrases(tag)
                    for phrase, weight in phrases:
                        if not self.is_spam_term(phrase):
                            if phrase in terms:
                                terms[phrase] += self.term_weights['context_bonus']
                            else:
                                terms[phrase] = weight
        
        # Final filtering
        filtered_terms = [(term, weight) for term, weight in terms.items() 
                         if len(term) > 2 and 
                         not all(word in self.stop_words for word in term.split())]
        
        # Only keep the most relevant terms
        filtered_terms.sort(key=lambda x: (x[1], len(x[0].split())), reverse=True)
        top_terms = filtered_terms[:5]  # Limit to top 5 most relevant terms
        
        for term, weight in top_terms:
            print(f"Extracted term: '{term}' with weight: {weight}")
            
        return top_terms
    def is_spam_term(self, term: str) -> bool:
        """Enhanced spam term detection"""
        term_lower = term.lower()
        words = term_lower.split()
        
        # Check word length
        if len(term_lower) <= 2:
            return True
            
        # Check against categorized spam indicators
        for suffix in self.spam_indicators['common_suffixes']:
            if any(word.endswith(suffix) for word in words):
                return True
                
        for prefix in self.spam_indicators['generic_prefixes']:
            if any(word.startswith(prefix) for word in words):
                return True
                
        if any(word in self.spam_indicators['marketing_terms'] for word in words):
            return True
            
        if any(word in self.spam_indicators['trend_riders'] for word in words):
            return True
        
        # Check suspicious patterns
        if any(re.search(pattern, term) for pattern in self.spam_indicators['suspicious_patterns']):
            return True
        
        return False


    def calculate_match_score(self, token_name: str, token_symbol: str, search_term: str, term_weight: float) -> float:
        try:
            score = 0.0
            token_name = str(token_name).lower()
            token_symbol = str(token_symbol).lower()
            search_term = str(search_term).lower()
            
            if search_term == token_name:
                score += 5.0 * float(term_weight)
            elif search_term == token_symbol:
                score += 4.0 * float(term_weight)
                
            elif search_term in token_name.split():
                position = token_name.split().index(search_term)
                score += (3.0 - (position * 0.5)) * float(term_weight)
            elif search_term in token_symbol.split():
                score += 2.0 * float(term_weight)
            
                name_similarity = self.calculate_similarity(search_term, token_name)
                if name_similarity > 0.8:
                    score += 2.0 * name_similarity * float(term_weight)
            
            return float(score)
            
        except Exception as e:
            print(f"Error in match score calculation: {e}")
            return 0.0
    def create_ngrams(self, text: str, n: int) -> Set[str]:
        text = re.sub(r'[^\w\s]', '', text.lower())
        return set(text[i:i+n] for i in range(len(text) - n + 1))
    def search_dexscreener(self, search_term: str) -> List[Dict]:
        url = f"{self.dexscreener_base_url}/search/?q={search_term}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            pairs = response.json().get('pairs', [])
            print(f"Found {len(pairs)} pairs for search term '{search_term}'")
            return pairs
        except Exception as e:
            print(f"Error searching DexScreener: {e}")
            return []


    def analyze_market_metrics(self, token_data: Dict) -> Tuple[float, Dict]:
        """Enhanced market metrics analysis including market cap"""
        score = 0.0
        feedback = {
            'liquidity': {'status': 'fail', 'value': 0, 'score': 0},
            'volume': {
                'status': 'fail',
                'h1': 0,
                'h6': 0,
                'h24': 0,
                'score': 0
            },
            'market_cap': {'status': 'fail', 'value': 0, 'score': 0},
            'price': {
                'current': 0,
                'changes': {
                    'h1': 0,
                    'h6': 0,
                    'h24': 0
                }
            }
        }
        
        try:
            # Get basic metrics
            liquidity_usd = float(token_data.get('liquidity', {}).get('usd', 0))
            volume_data = token_data.get('volume', {})
            volume_24h = float(volume_data.get('h24', 0))
            volume_6h = float(volume_data.get('h6', 0))
            volume_1h = float(volume_data.get('h1', 0))
            
            # Calculate market cap with FDV fallback
            price_usd = float(token_data.get('priceUsd', 0))
            market_cap = float(token_data.get('fdv', 0))  # Try FDV first
            
            if not market_cap:  # If FDV not available, calculate from total supply
                total_supply = float(token_data.get('baseToken', {}).get('totalSupply', 0))
                market_cap = price_usd * total_supply if price_usd and total_supply else 0
            
            # Check market cap
            feedback['market_cap']['value'] = market_cap
            if market_cap >= self.min_requirements['market_cap']:
                feedback['market_cap']['status'] = 'pass'
                for threshold in self.market_weights['market_cap']['thresholds']:
                    if market_cap >= threshold:
                        score += self.market_weights['market_cap']['weight']
                        feedback['market_cap']['score'] += self.market_weights['market_cap']['weight']
            
                # Check liquidity
            feedback['liquidity']['value'] = liquidity_usd
            if liquidity_usd >= self.min_requirements['liquidity_usd']:
                feedback['liquidity']['status'] = 'pass'
                for threshold in self.market_weights['liquidity']['thresholds']:
                    if liquidity_usd >= threshold:
                        score += self.market_weights['liquidity']['weight']
                        feedback['liquidity']['score'] += self.market_weights['liquidity']['weight']
            
            # Check volume
            feedback['volume'].update({
                'h1': volume_1h,
                'h6': volume_6h,
                'h24': volume_24h
            })
            
            if volume_24h >= self.min_requirements['volume_24h']:
                feedback['volume']['status'] = 'pass'
                for threshold in self.market_weights['volume']['thresholds']:
                    if volume_24h >= threshold:
                        score += self.market_weights['volume']['weight']
                        feedback['volume']['score'] += self.market_weights['volume']['weight']
            
            # Record price data but don't score it
            current_price = float(token_data.get('priceUsd', 0))
            price_changes = token_data.get('priceChange', {})
            feedback['price'].update({
                'current': current_price,
                'changes': {
                    'h1': float(price_changes.get('h1', 0)),
                    'h6': float(price_changes.get('h6', 0)),
                    'h24': float(price_changes.get('h24', 0))
                }
            })
            
            
            if self.debug_mode:
                print("\nMarket Analysis:")
                print(f"Market Cap: ${market_cap:,.2f} (Score: {feedback['market_cap']['score']})")
                print(f"Liquidity: ${liquidity_usd:,.2f} (Score: {feedback['liquidity']['score']})")
                print(f"Volume 24h: ${volume_24h:,.2f} (Score: {feedback['volume']['score']})")
                print(f"Total Market Score: {score}")
            
        except Exception as e:
            print(f"Error in market analysis: {e}")
            return 0.0, feedback
        
        return float(score), feedback
    def analyze_token_relevance(self, token_data: Dict, search_term: str, term_weight: float, meme_data: Dict) -> float:
        """Calculate token relevance score with proper type handling"""
        token_name = token_data.get('baseToken', {}).get('name', '')
        token_symbol = token_data.get('baseToken', {}).get('symbol', '')
        
        if not token_name or not token_symbol:
            return 0.0
            
        # Initial filtering
        if self.is_spam_token(token_name, token_symbol):
            return 0.0
            
        # Match scoring
        match_score = self.calculate_match_score(token_name, token_symbol, search_term, term_weight)
        if match_score == 0:
            return 0.0
            
        # Add market metrics - ensure we're getting just the score
        market_score, _ = self.analyze_market_metrics(token_data)
        final_score = match_score + market_score
        
        # Add temporal relevance
        temporal_score = self.analyze_temporal_relevance(token_data, meme_data)
        final_score += temporal_score
        
        return max(0, final_score)
    def is_spam_token(self, name: str, symbol: str) -> bool:
        """Check if token appears to be spam"""
        name_lower = name.lower()
        symbol_lower = symbol.lower()
        
        # Check for spam indicators
        if any(indicator in name_lower.split() or indicator in symbol_lower.split() 
               for indicator in self.spam_indicators):
            return True
            
        # Check suspicious patterns
        suspicious_patterns = [
            r'\d{3,}',
            r'[A-Z]{5,}',
            r'[A-Z][a-z]+[A-Z]',
            r'[!@#$%^&*()_+=\[\]{};:"|<>?]',
            r'v[0-9]',
            r'[0-9]x',
        ]
        
        return any(re.search(pattern, name) for pattern in suspicious_patterns)


    def analyze_temporal_relevance(self, token_data: Dict, meme_data: Dict) -> float:
        """
        Analyze temporal relevance between token creation and meme popularity.
        
        Args:
            token_data (Dict): Token information from DexScreener
            meme_data (Dict): Meme information from KYM
            
        Returns:
            float: Temporal relevance score
        """
        try:
            score = 0.0
            
            # Get token creation timestamp with debug logging
            created_timestamp = token_data.get('pairCreatedAt', '0')
            if self.debug_mode:
                print(f"Raw timestamp value: {created_timestamp} (type: {type(created_timestamp)})")
            
            # Handle various timestamp formats
            if isinstance(created_timestamp, str):
                # Remove any non-numeric characters
                created_timestamp = ''.join(filter(str.isdigit, created_timestamp))
                if not created_timestamp:
                    if self.debug_mode:
                        print("No valid digits found in timestamp string")
                    return 0.0
            
            # Convert to integer, handling milliseconds if present
            try:
                created_timestamp = int(float(str(created_timestamp)))
                # If timestamp is in milliseconds, convert to seconds
                if created_timestamp > 9999999999:
                    created_timestamp = created_timestamp // 1000
            except (ValueError, TypeError) as e:
                if self.debug_mode:
                    print(f"Failed to convert timestamp: {e}")
                return 0.0
                
            if created_timestamp == 0:
                if self.debug_mode:
                    print("Timestamp is zero")
                return 0.0
                
            try:
                # Convert token creation time to UTC datetime
                token_created = datetime.fromtimestamp(created_timestamp, tz=timezone.utc)
                if self.debug_mode:
                    print(f"Successfully parsed timestamp to: {token_created}")
            except (ValueError, OSError) as e:
                if self.debug_mode:
                    print(f"Failed to create datetime from timestamp: {e}")
                return 0.0
                
            current_time = datetime.now(timezone.utc)
            
            # Calculate token age in days
            token_age_days = (current_time - token_created).days
            
            if self.debug_mode:
                print(f"Token age in days: {token_age_days}")
            
            # Score based on token age
            if 0 <= token_age_days < 1:
                score += 1.0  # Very new tokens (less than 1 day)
            elif 1 <= token_age_days < 7:
                score += 0.5  # Week old tokens
            elif 7 <= token_age_days < 30:
                score += 0.25  # Month old tokens
                
            # Get meme added date if available
            meme_added = meme_data.get('added')
            if meme_added and self.debug_mode:
                print(f"Meme added date: {meme_added}")
                
            if meme_added:
                try:
                    # Remove timezone indicator if present
                    meme_added = meme_added.replace('Z', '').replace('+00:00', '')
                    
                    # Try parsing meme date
                    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S'):
                        try:
                            meme_date = datetime.strptime(meme_added, fmt)
                            meme_date = meme_date.replace(tzinfo=timezone.utc)
                            
                            # Calculate days between meme and token
                            days_diff = abs((token_created - meme_date).days)
                            
                            if self.debug_mode:
                                print(f"Days between meme and token: {days_diff}")
                            
                            # Add temporal correlation score
                            if days_diff < 7:
                                score += 1.0  # High correlation
                            elif days_diff < 30:
                                score += 0.5  # Medium correlation
                                
                            break
                        except ValueError:
                            if self.debug_mode:
                                print(f"Failed to parse date with format {fmt}")
                            continue
                            
                except Exception as date_error:
                    if self.debug_mode:
                        print(f"Error parsing meme date: {date_error}")
                    
            if self.debug_mode:
                print(f"Final temporal score: {score}")
                
            return float(score)
            
        except Exception as e:
            if self.debug_mode:
                print(f"Error in temporal analysis: {e}")
            return 0.0
    def format_enhanced_result(self, token_data: Dict, meme_name: str, search_term: str, term_weight: float, score: float) -> Dict:
        """Enhanced result formatting with detailed metrics including market cap, chart analysis, and better date handling"""
        try:
            base_token = token_data.get('baseToken', {})
            price_changes = token_data.get('priceChange', {})
            volumes = token_data.get('volume', {})
            
            # Add dex links
            dex_id = token_data.get('dexId', '')
            chain_id = token_data.get('chainId', '').lower()
            pair_address = token_data.get('pairAddress', '')
            
            dex_links = self.generate_dex_links(dex_id, chain_id, pair_address)
            
            # Add social/community links if available from baseToken
            social_links = {
                'telegram': base_token.get('telegram', ''),
                'twitter': base_token.get('twitter', ''),
                'website': base_token.get('website', ''),
                'discord': base_token.get('discord', ''),
                'medium': base_token.get('medium', '')
            }
            
            # Filter out empty social links
            social_links = {k: v for k, v in social_links.items() if v}
            
            # Calculate market cap
            try:
                price_usd = float(token_data.get('priceUsd', 0))
                fdv = token_data.get('fdv')  # Fully Diluted Valuation if available
                market_cap = 0
                
                if fdv:
                    try:
                        market_cap = float(fdv)
                    except (ValueError, TypeError):
                        market_cap = 0
                else:
                    # Fallback to calculating from total supply if available
                    total_supply = base_token.get('totalSupply')
                    if total_supply and price_usd:
                        try:
                            market_cap = float(total_supply) * price_usd
                        except (ValueError, TypeError):
                            market_cap = 0
            except Exception as e:
                print(f"Error calculating market cap: {e}")
                price_usd = 0
                market_cap = 0

            # Handle creation date/age
            created_at = "Unknown"
            try:
                pair_created = token_data.get('pairCreatedAt')
                if pair_created:
                    if isinstance(pair_created, (int, float)):
                        # Convert timestamp to days ago
                        current_time = int(time.time())
                        if pair_created > 9999999999:  # Convert from milliseconds if needed
                            pair_created = pair_created / 1000
                        days_ago = int((current_time - pair_created) / 86400)  # 86400 seconds in a day
                        hours_ago = int(((current_time - pair_created) % 86400) / 3600)
                        created_at = f"{days_ago}d {hours_ago}h ago"
                    elif isinstance(pair_created, str):
                        if 'd' in pair_created and 'h' in pair_created:
                            created_at = pair_created
            except Exception as e:
                print(f"Error calculating creation date: {e}")
                created_at = "Unknown"
                
            # Get chart analysis if available
            chart_analysis = {}
            try:
                chart_data = self.chart_analyzer.get_price_chart(pair_address, chain_id)
                if chart_data is not None:
                    emas = self.chart_analyzer.calculate_ema(chart_data)
                    chart_analysis = self.chart_analyzer.analyze_ema_signals(chart_data, emas)
            except Exception as e:
                print(f"Error getting chart analysis: {e}")
            
            # Prepare the result dictionary
            result = {
                'meme': meme_name,
                'token': base_token.get('name', ''),
                'symbol': base_token.get('symbol', ''),
                'address': base_token.get('address', ''),
                'pair_address': token_data.get('pairAddress', ''),
                'dex': token_data.get('dexId', ''),
                'chain': token_data.get('chainId', ''),
                'liquidity_usd': token_data.get('liquidity', {}).get('usd', 0),
                'volume': {
                    'h1': volumes.get('h1', 0),
                    'h6': volumes.get('h6', 0),
                    'h24': volumes.get('h24', 0)
                },
                'price_usd': price_usd,
                'price_native': token_data.get('priceNative', 'Unknown'),
                'price_changes': {
                    'h1': price_changes.get('h1', 'Unknown'),
                    'h6': price_changes.get('h6', 'Unknown'),
                    'h24': price_changes.get('h24', 'Unknown')
                },
                'market_cap': market_cap,
                'total_supply': base_token.get('totalSupply', 'Unknown'),
                'txns_24h': {
                    'buys': token_data.get('txns', {}).get('h24', {}).get('buys', 0),
                    'sells': token_data.get('txns', {}).get('h24', {}).get('sells', 0)
                },
                'created_at': created_at,
                'score': score,
                'search_term': search_term,
                'term_weight': term_weight,
                'dex_links': dex_links,
                'social_links': social_links,
                'explorer_url': self.searcher.get_explorer_url(chain_id, base_token.get('address', '')),
                'technical_analysis': {
                    'chart_data_available': bool(chart_analysis),
                    'ema_analysis': chart_analysis,
                    'last_updated': datetime.now().isoformat() if chart_analysis else None
                }
            }
            
            return result
            
        except Exception as e:
            print(f"Error formatting result: {e}")
            # Return a minimal valid result if there's an error
            return {
                'meme': meme_name,
                'token': base_token.get('name', ''),
                'symbol': base_token.get('symbol', ''),
                'address': base_token.get('address', ''),
                'score': score,
                'search_term': search_term,
                'term_weight': term_weight,
                'created_at': 'Unknown'
            }
    def format_timestamp(self, timestamp: int) -> str:
        """Format timestamp safely with better error handling"""
        try:
            if not timestamp or timestamp == 0:
                return "Unknown"
                
            if timestamp > 9999999999:
                timestamp = timestamp // 1000
                
            if timestamp < 0 or timestamp > 9999999999:
                return "Unknown"
                
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.isoformat()
        except (ValueError, OSError, OverflowError) as e:
            print(f"Timestamp formatting error: {e}")
            return "Unknown"
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using SequenceMatcher"""
        try:
            return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def normalize_text(self, text: str) -> str:
        """Normalize text for matching"""
        try:
            if not text:
                return ""
            # Remove special characters except spaces
            text = re.sub(r'[^\w\s]', ' ', text)
            # Normalize whitespace
            text = ' '.join(text.split())
            return text
        except Exception as e:
            print(f"Error normalizing text: {e}")
            return ""
    def get_explorer_url(self, chain: str, address: str) -> str:
        """Get blockchain explorer URL"""
        explorers = {
            'ethereum': 'https://etherscan.io/address/',
            'bsc': 'https://bscscan.com/address/',
            'solana': 'https://solscan.io/account/',
            'arbitrum': 'https://arbiscan.io/address/',
            'polygon': 'https://polygonscan.com/address/',
            'avalanche': 'https://snowtrace.io/address/',
            'fantom': 'https://ftmscan.com/address/',
            'optimism': 'https://optimistic.etherscan.io/address/',
            'base': 'https://basescan.org/address/'
        }
        
        base_url = explorers.get(chain.lower(), '')
        if base_url and address:
            return f"{base_url}{address}"
        return ''
    

