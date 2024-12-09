from typing import List, Dict, Any, Tuple
import json
from datetime import datetime, timedelta
from googleapiclient.discovery import build
import re
from collections import Counter
import numpy as np
class YoutubeMemeChecker:
    def __init__(self, api_key: str):
        """Initialize with YouTube API key."""
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.api_calls = {
            'search': {'cost': 100, 'count': 0},
            'videos': {'cost': 1, 'count': 0},
            'total_quota': 0
        }
        self.DAILY_QUOTA = 10000
    def get_quota_status(self) -> Dict[str, Any]:
        """Calculate remaining API quota and estimated costs."""
        total_used = self.api_calls['total_quota']
        remaining = self.DAILY_QUOTA - total_used
        
        estimated_cost_per_meme = (
            100 +  
            1 * 50  
        
        remaining_memes = remaining // estimated_cost_per_meme
        
        return {
            'quota_used': total_used,
            'quota_remaining': remaining,
            'estimated_memes_remaining': remaining_memes,
            'calls_made': {
                'search_calls': self.api_calls['search']['count'],
                'video_detail_calls': self.api_calls['videos']['count']
            }
        }
   
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        return re.findall(r'#(\w+)', text)
        
    def clean_search_term(self, meme_name: str) -> str:
        """Clean meme name and handle hashtags for YouTube search."""
        # Extract hashtags before cleaning
        hashtags = self.extract_hashtags(meme_name)
        
        # Clean the main text
        cleaned = re.sub(r'[^\w\s]', ' ', meme_name).strip()
        
        # Add relevant hashtags back as search terms
        gaming_related = {'gaming', 'game', 'games', 'gamer'}
        relevant_hashtags = [tag for tag in hashtags 
                           if len(tag) > 2 and  # Skip very short tags
                           tag.lower() not in gaming_related]  # Skip generic gaming tags
        
        if relevant_hashtags:
            cleaned += ' ' + ' '.join(relevant_hashtags)
            
        return cleaned
    def search_youtube(self, search_term: str, max_results: int = 50) -> Tuple[List[Dict], Dict[str, Any]]:
        """Search YouTube with quota tracking."""
        try:
            self.api_calls['search']['count'] += 1
            self.api_calls['total_quota'] += self.api_calls['search']['cost']
            
            search_response = self.youtube.search().list(
                q=search_term,
                part='id,snippet',
                type='video',
                order='relevance',
                maxResults=max_results,
                publishedAfter=(datetime.utcnow() - timedelta(days=365)).isoformat() + 'Z'
            ).execute()
            
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                return [], self.get_quota_status()
            
            self.api_calls['videos']['count'] += 1
            self.api_calls['total_quota'] += len(video_ids) * self.api_calls['videos']['cost']
            
            videos_response = self.youtube.videos().list(
                part='statistics,snippet',
                id=','.join(video_ids)
            ).execute()
            
            results = []
            for video in videos_response.get('items', []):
                stats = video['statistics']
                results.append({
                    'video_id': video['id'],
                    'title': video['snippet']['title'],
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0)),
                    'published_at': video['snippet']['publishedAt']
                })
            
            return sorted(results, key=lambda x: x['views'], reverse=True), self.get_quota_status()
            
        except Exception as e:
            print(f"Error searching YouTube for {search_term}: {str(e)}")
            return [], self.get_quota_status()
    def analyze_virality(self, videos: List[Dict]) -> Dict[str, Any]:
        """Enhanced video analysis with better growth metrics and recent video indicators."""
        if not videos:
            return {}

        current_time = datetime.utcnow()
        
        # Initialize metrics
        detailed_videos = []
        recent_videos = []
        platforms_mentioned = Counter()
        
        time_periods = {
            'last_day': {'videos': [], 'views': 0},
            'last_week': {'videos': [], 'views': 0},
            'last_month': {'videos': [], 'views': 0},
            'previous_week': {'videos': [], 'views': 0}
        }
        
        for video in videos:
            publish_date = datetime.strptime(video['published_at'], '%Y-%m-%dT%H:%M:%SZ')
            age_days = (current_time - publish_date).days
            views = int(video.get('views', 0))
            likes = int(video.get('likes', 0))
            comments = int(video.get('comments', 0))
            title = video['title'].lower()
            
            daily_views = views / max(1, age_days) if age_days > 0 else views
            
            video_info = {
                'title': video['title'],
                'views': views,
                'daily_views': daily_views,
                'url': f"https://youtube.com/watch?v={video['video_id']}",
                'age_days': age_days,
                'publish_date': publish_date,
                'is_recent': age_days <= 7  # Flag for videos in last 7 days
            }
            
            if age_days <= 1:
                time_periods['last_day']['videos'].append(video_info)
                time_periods['last_day']['views'] += views
                
            if age_days <= 7:
                time_periods['last_week']['videos'].append(video_info)
                time_periods['last_week']['views'] += views
                
            elif age_days <= 14:  # Previous week (7-14 days ago)
                time_periods['previous_week']['videos'].append(video_info)
                time_periods['previous_week']['views'] += views
                
            if age_days <= 30:
                time_periods['last_month']['videos'].append(video_info)
                time_periods['last_month']['views'] += views
                recent_videos.append(video_info)
                
            # Platform detection with improved accuracy
            detected_platforms = set()
            platform_keywords = {
                'tiktok': ['#tiktok', ' tt ', 'douyin'],
                'youtube': ['youtube shorts', '#shorts', '#youtube'],
                'instagram': ['#instagram', '#reels', ' ig '],
                'twitter': ['#twitter', '#tweet', 'x.com'],
                'facebook': ['#facebook', '#fb', '#meta']
            }
            
            for platform, keywords in platform_keywords.items():
                if any(keyword in f" {title} " for keyword in keywords):
                    detected_platforms.add(platform)
                    platforms_mentioned[platform] += 1
            
            detailed_videos.append(video_info)
        
        detailed_videos.sort(key=lambda x: x['views'], reverse=True)
        recent_videos.sort(key=lambda x: x['views'], reverse=True)
        
        this_week_views = time_periods['last_week']['views']
        prev_week_views = time_periods['previous_week']['views']
        
        if prev_week_views > 0:
            weekly_growth = ((this_week_views - prev_week_views) / prev_week_views) * 100
        else:
            weekly_growth = 100 if this_week_views > 0 else 0
        
        view_rates = [v['daily_views'] for v in detailed_videos if v['daily_views'] > 0]
        viral_threshold = (
            max(50000, np.percentile(view_rates, 90))
            if view_rates else 50000
        )
        
        viral_videos = [v for v in detailed_videos if v['daily_views'] > viral_threshold]
        
        trending_score = 0
        
        if weekly_growth > 200: trending_score += 3
        elif weekly_growth > 100: trending_score += 2
        elif weekly_growth > 50: trending_score += 1
        
        recent_count = len(time_periods['last_week']['videos'])
        if recent_count >= 10: trending_score += 3
        elif recent_count >= 5: trending_score += 2
        elif recent_count >= 2: trending_score += 1
        
        if len(viral_videos) >= 3: trending_score += 4
        elif len(viral_videos) >= 1: trending_score += 2

        return {
            'videos': detailed_videos[:10],
            'recent_videos': recent_videos[:5],
            'stats': {
                'week_views': this_week_views,
                'prev_week_views': prev_week_views,
                'weekly_growth': round(weekly_growth, 1),
                'daily_view_rate': round(this_week_views / 7, 1) if this_week_views > 0 else 0,
                'viral_threshold': viral_threshold,
                'trending_score': trending_score,
                'video_counts': {
                    'last_day': len(time_periods['last_day']['videos']),
                    'last_week': len(time_periods['last_week']['videos']),
                    'last_month': len(time_periods['last_month']['videos'])
                }
            },
            'platforms': dict(platforms_mentioned),
            'viral_videos': [{
                'title': v['title'],
                'views': v['views'],
                'daily_views': v['daily_views'],
                'url': v['url']
            } for v in viral_videos[:5]]
        }
    def analyze_video_timeline(self, videos: List[Dict]) -> Dict[str, Any]:
        if not videos:
            return {
                'timeline': {
                    'last_day': 0,
                    'last_week': 0,
                    'last_month': 0,
                    'last_3_months': 0,
                    'last_year': 0
                },
                'total_views': 0,
                'recent_views': 0,
                'trend_score': 0,
                'trend_factors': [],
                'is_trending': False
            }
            
        current_time = datetime.utcnow()
        
        timeline = {
            'last_day': 0,
            'last_week': 0,
            'last_month': 0,
            'last_3_months': 0,
            'last_year': 0
        }
        
        total_views = 0
        recent_views = 0  
        
        for video in videos:
            try:
                publish_date = datetime.strptime(video['published_at'], '%Y-%m-%dT%H:%M:%SZ')
                days_ago = (current_time - publish_date).days
                views = int(video.get('views', 0))
                
                total_views += views
                
                if days_ago <= 30:
                    recent_views += views
                
                if days_ago <= 1:
                    timeline['last_day'] += 1
                if days_ago <= 7:
                    timeline['last_week'] += 1
                if days_ago <= 30:
                    timeline['last_month'] += 1
                if days_ago <= 90:
                    timeline['last_3_months'] += 1
                if days_ago <= 365:
                    timeline['last_year'] += 1
                    
            except (ValueError, TypeError) as e:
                print(f"Error processing video date: {e}")
                continue
        
        trend_score = 0
        trend_factors = []
        
        if timeline['last_week'] >= 10:
            trend_score += 3
            trend_factors.append('Very high recent video volume')
        elif timeline['last_week'] >= 5:
            trend_score += 2
            trend_factors.append('High recent video volume')
        elif timeline['last_week'] >= 3:
            trend_score += 1
            trend_factors.append('Moderate recent video volume')
        
        weekly_rate = timeline['last_week'] / 7
        monthly_rate = timeline['last_month'] / 30
        if weekly_rate > monthly_rate * 2:
            trend_score += 3
            trend_factors.append('Accelerating video production')
        elif weekly_rate > monthly_rate * 1.5:
            trend_score += 2
            trend_factors.append('Growing video production')
        
        if total_views > 0:
            recent_view_ratio = recent_views / total_views
            if recent_view_ratio > 0.5:
                trend_score += 3
                trend_factors.append('Strong recent view momentum')
            elif recent_view_ratio > 0.25:
                trend_score += 2
                trend_factors.append('Good recent view momentum')
        
        return {
            'timeline': timeline,
            'total_views': total_views,
            'recent_views': recent_views,
            'trend_score': trend_score,
            'trend_factors': trend_factors,
            'is_trending': trend_score >= 5
    }
    def process_meme_file(self, json_file_path: str, limit: int = 10) -> Dict[str, Any]:
        """Process memes from JSON file and analyze YouTube trends."""
        trending_memes = []
        processed_count = 0
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                memes_data = data.get('memes', [])
            
            for meme in memes_data[:limit]:
                processed_count += 1
                meme_name = meme.get('name', '')
                if not meme_name:
                    continue
                
                print(f"Processing meme {processed_count}/{limit}: {meme_name}")
                
                search_term = self.clean_search_term(meme_name)
                youtube_results, quota_status = self.search_youtube(search_term)
                
                if youtube_results:
                    trend_analysis = self.analyze_video_timeline(youtube_results)
                    virality_metrics = self.analyze_virality(youtube_results)
                    
                    trending_memes.append({
                        'meme_name': meme_name,
                        'youtube_metrics': {
                            'total_videos': len(youtube_results),
                            'total_views': trend_analysis['total_views'],
                            'recent_views': trend_analysis['recent_views'],
                            'timeline': trend_analysis['timeline'],
                            'trend_score': trend_analysis['trend_score'],
                            'trend_factors': trend_analysis['trend_factors'],
                            'is_trending': trend_analysis['is_trending'],
                            'virality': virality_metrics,
                            'top_videos': youtube_results[:5]
                        },
                        'original_url': meme.get('url', ''),
                        'year': meme.get('year', 'Unknown'),
                        'hashtags': self.extract_hashtags(meme_name)
                    })
        
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return {
                'trending_memes': [],
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'memes_processed': 0,
                'quota_status': self.get_quota_status()
            }
        
        return {
            'trending_memes': sorted(trending_memes, 
                                   key=lambda x: (x['youtube_metrics']['trend_score'], 
                                                x['youtube_metrics']['recent_views']), 
                                   reverse=True),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'memes_processed': processed_count,
            'quota_status': self.get_quota_status()
        }

def print_trend_report(report: Dict[str, Any]):
    print(f"\n=== YouTube Meme Trend Analysis ({report['analysis_date']}) ===")
    print(f"Memes Processed: {report['memes_processed']}")
    
    quota = report['quota_status']
    print(f"\n📊 API Quota Status: {quota['quota_used']:,} used, {quota['quota_remaining']:,} remaining")
    
    if report['trending_memes']:
        print("\n🔥 Top Trending Memes on YouTube:")
        for i, meme in enumerate(report['trending_memes'], 1):
            metrics = meme['youtube_metrics']
            virality = metrics['virality']
            stats = virality['stats']
            counts = stats['video_counts']
            
            print(f"\n{i}. {meme['meme_name']}")
            if meme['hashtags']:
                print(f"   #{' #'.join(meme['hashtags'])}")
            
            print(f"\n   📈 Performance Metrics:")
            print(f"   Trending Score: {stats['trending_score']}/10")
            print(f"   Recent Activity: {counts['last_day']} today, {counts['last_week']} this week")
            print(f"   Total Views This Week: {stats['week_views']:,}")
            print(f"   Previous Week Views: {stats['prev_week_views']:,}")
            print(f"   Weekly Growth: {stats['weekly_growth']:+.1f}%")
            print(f"   Avg Daily Views: {stats['daily_view_rate']:,.1f}")
            
            if virality['recent_videos']:
                print(f"\n   🎥 Recent Videos (Last 30 days):")
                for vid in virality['recent_videos']:
                    recent_indicator = "🆕 " if vid.get('is_recent') else "   "
                    print(f"      {recent_indicator}• {vid['title']}")
                    print(f"        {vid['views']:,} views ({vid['daily_views']:,.1f}/day)")
                    print(f"        {vid['url']}")
            
            if virality['viral_videos']:
                print(f"\n   🚀 Viral Videos (>{stats['viral_threshold']:,.0f} views/day):")
                for vid in virality['viral_videos']:
                    print(f"      • {vid['title']}")
                    print(f"        {vid['views']:,} views ({vid['daily_views']:,.1f}/day)")
                    print(f"        {vid['url']}")
            
            if virality['platforms']:
                print(f"\n   📱 Platform Distribution:")
                for platform, count in virality['platforms'].items():
                    print(f"      • {platform.title()}: {count} videos")
            
            print("\n   " + "="*50)
if __name__ == "__main__":
    API_KEY = ''
    checker = YoutubeMemeChecker(API_KEY)
    report = checker.process_meme_file("", limit=1500)
    print_trend_report(report)
