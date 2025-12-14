import re
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from app.config import get_settings


LOGIN_WALL_KEYWORDS = [
    "sign in",
    "sign up",
    "join linkedin",
    "login-submit",
    "session_key",
    "authwall",
    "please log in",
    "join now",
]

INVALID_COMPANY_NAMES = [
    "sign in",
    "linkedin",
    "join now",
    "sign up",
    "",
    None,
]


class ScrapingException(Exception):
    def __init__(self, message: str, is_login_wall: bool = False, retryable: bool = True):
        self.message = message
        self.is_login_wall = is_login_wall
        self.retryable = retryable
        super().__init__(message)


class LoginWallException(ScrapingException):
    def __init__(self, page_id: str):
        super().__init__(
            f"LinkedIn login wall detected for page '{page_id}'. "
            "Page requires authentication to access full data.",
            is_login_wall=True,
            retryable=False,
        )
        self.page_id = page_id


@dataclass
class ScrapedPageData:
    page_id: str
    name: str
    url: str
    linkedin_id: Optional[str] = None
    profile_picture_url: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    follower_count: int = 0
    headcount: Optional[str] = None
    specialities: List[str] = field(default_factory=list)
    founded: Optional[str] = None
    headquarters: Optional[str] = None
    company_type: Optional[str] = None


@dataclass
class ScrapedPostData:
    post_id: str
    page_id: str
    content: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    post_url: Optional[str] = None
    posted_at: Optional[datetime] = None


@dataclass
class ScrapedCommentData:
    comment_id: str
    post_id: str
    page_id: str
    author_name: str
    content: str
    author_profile_url: Optional[str] = None
    author_headline: Optional[str] = None
    like_count: int = 0
    commented_at: Optional[datetime] = None


@dataclass
class ScrapedEmployeeData:
    page_id: str
    name: str
    designation: Optional[str] = None
    location: Optional[str] = None
    profile_url: Optional[str] = None
    profile_picture_url: Optional[str] = None


class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com/company"

    def __init__(self):
        self.settings = get_settings()
        self.driver: Optional[webdriver.Chrome] = None

    def _init_driver(self) -> webdriver.Chrome:
        import os
        import glob

        options = Options()

        if self.settings.scraper_headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver_path = None
        try:
            wdm_path = os.path.expanduser("~/.wdm/drivers/chromedriver")
            if os.path.exists(wdm_path):
                matches = glob.glob(f"{wdm_path}/**/chromedriver", recursive=True)
                for match in matches:
                    if os.path.isfile(match) and os.access(match, os.X_OK):
                        driver_path = match
                        break

            if not driver_path:
                installed_path = ChromeDriverManager().install()
                if "THIRD_PARTY" in installed_path or "LICENSE" in installed_path:
                    driver_dir = os.path.dirname(installed_path)
                    driver_path = os.path.join(driver_dir, "chromedriver")
                else:
                    driver_path = installed_path

            print(f"🔧 Using chromedriver: {driver_path}")
            service = Service(driver_path)
        except Exception as e:
            print(f"⚠️ WebDriver manager failed: {e}, trying system chromedriver")
            service = Service()

        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(self.settings.scraper_page_load_timeout)
        driver.implicitly_wait(self.settings.scraper_implicit_wait)

        return driver

    def _get_driver(self) -> webdriver.Chrome:
        if self.driver is None:
            self.driver = self._init_driver()
        return self.driver

    def close(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _wait_for_page_load(self, timeout: int = 10) -> None:
        driver = self._get_driver()
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def _scroll_page(self, scroll_count: int = 3, delay: float = 1.0) -> None:
        driver = self._get_driver()
        for _ in range(scroll_count):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(delay)

    def _is_login_wall(self, page_source: str) -> bool:
        if not page_source:
            return True

        page_lower = page_source.lower()

        for keyword in LOGIN_WALL_KEYWORDS:
            if keyword in page_lower:
                indicator_count = sum(1 for k in LOGIN_WALL_KEYWORDS if k in page_lower)
                if indicator_count >= 2:
                    return True

        if 'name="session_key"' in page_lower or 'id="session_key"' in page_lower:
            return True

        return False

    def _is_valid_company_name(self, name: Optional[str]) -> bool:
        if not name:
            return False

        name_lower = name.lower().strip()

        for invalid in INVALID_COMPANY_NAMES:
            if invalid is None:
                continue
            if invalid == name_lower:
                return False

        if len(name_lower) < 2:
            return False

        return True

    def _validate_scraped_page(self, page_data: Optional['ScrapedPageData'], page_source: str) -> None:
        if self._is_login_wall(page_source):
            raise LoginWallException(page_data.page_id if page_data else "unknown")

        if not page_data:
            raise ScrapingException("Failed to extract page data", retryable=True)

        if not self._is_valid_company_name(page_data.name):
            raise LoginWallException(page_data.page_id)

    def _parse_follower_count(self, text: str) -> int:
        if not text:
            return 0

        text = text.lower().replace(",", "").replace(" followers", "").replace(" follower", "").strip()

        try:
            if "m" in text:
                return int(float(text.replace("m", "")) * 1_000_000)
            elif "k" in text:
                return int(float(text.replace("k", "")) * 1_000)
            else:
                return int(float(text))
        except (ValueError, AttributeError):
            return 0

    def _parse_engagement_count(self, text: str) -> int:
        if not text:
            return 0

        text = text.lower().replace(",", "").strip()

        try:
            match = re.search(r"([\d.]+)\s*([km])?", text)
            if match:
                num = float(match.group(1))
                suffix = match.group(2)
                if suffix == "k":
                    return int(num * 1_000)
                elif suffix == "m":
                    return int(num * 1_000_000)
                return int(num)
        except (ValueError, AttributeError):
            pass
        return 0

    def _generate_post_id(self, page_id: str, content: str, index: int) -> str:
        content_hash = hashlib.md5(
            f"{page_id}_{content[:100] if content else ''}_{index}".encode()
        ).hexdigest()[:12]
        return f"{page_id}_{content_hash}"

    def _generate_comment_id(self, post_id: str, author: str, content: str, index: int) -> str:
        content_hash = hashlib.md5(
            f"{post_id}_{author}_{content[:50] if content else ''}_{index}".encode()
        ).hexdigest()[:8]
        return f"{post_id}_c{content_hash}"

    async def scrape_page(self, page_id: str) -> Optional[ScrapedPageData]:
        driver = self._get_driver()
        url = f"{self.BASE_URL}/{page_id}/about/"

        try:
            driver.get(url)
            self._wait_for_page_load()
            time.sleep(2)

            page_source = driver.page_source

            if self._is_login_wall(page_source):
                print(f"🚫 Login wall detected for page: {page_id}")
                raise LoginWallException(page_id)

            soup = BeautifulSoup(page_source, "lxml")
            name = self._extract_company_name(soup, driver)

            if not self._is_valid_company_name(name):
                print(f"🚫 Invalid company name detected: '{name}' - likely login wall")
                raise LoginWallException(page_id)

            page_data = ScrapedPageData(
                page_id=page_id,
                name=name,
                url=f"https://www.linkedin.com/company/{page_id}/",
                linkedin_id=self._extract_linkedin_id(driver),
                profile_picture_url=self._extract_profile_picture(soup),
                description=self._extract_description(soup, driver),
                website=self._extract_website(soup, driver),
                industry=self._extract_industry(soup, driver),
                follower_count=self._extract_follower_count(soup, driver),
                headcount=self._extract_headcount(soup, driver),
                specialities=self._extract_specialities(soup, driver),
                founded=self._extract_founded(soup, driver),
                headquarters=self._extract_headquarters(soup, driver),
                company_type=self._extract_company_type(soup, driver),
            )

            self._validate_scraped_page(page_data, page_source)

            print(f"✅ Successfully scraped page: {page_id} - {name}")
            return page_data

        except LoginWallException:
            raise
        except TimeoutException:
            print(f"⏰ Timeout while loading page: {url}")
            raise ScrapingException(f"Timeout loading page {page_id}", retryable=True)
        except Exception as e:
            print(f"❌ Error scraping page {page_id}: {str(e)}")
            raise ScrapingException(f"Error scraping page {page_id}: {str(e)}", retryable=True)

    def _extract_company_name(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> Optional[str]:
        selectors = [
            "h1.org-top-card-summary__title",
            "h1[class*='org-top-card']",
            "span.org-top-card-summary__title",
            ".org-top-card-summary-info-list__info-item",
        ]

        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    return element.get_text(strip=True)
            except Exception:
                continue

        try:
            element = driver.find_element(By.CSS_SELECTOR, "h1")
            if element:
                return element.text.strip()
        except NoSuchElementException:
            pass

        return None

    def _extract_linkedin_id(self, driver: webdriver.Chrome) -> Optional[str]:
        try:
            current_url = driver.current_url
            match = re.search(r"/company/(\d+)", current_url)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    def _extract_profile_picture(self, soup: BeautifulSoup) -> Optional[str]:
        selectors = [
            "img.org-top-card-primary-content__logo",
            "img[class*='org-top-card']",
            ".org-top-card-primary-content__logo img",
            "img.EntityPhoto-square-5",
        ]

        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element and element.get("src"):
                    return element.get("src")
            except Exception:
                continue

        return None

    def _extract_description(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> Optional[str]:
        selectors = [
            "p.org-about-us-organization-description__text",
            ".org-about-us-organization-description__text",
            "section.org-about-module p",
            ".org-page-details-module__card-spacing p",
        ]

        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    return element.get_text(strip=True)
            except Exception:
                continue

        return None

    def _extract_website(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> Optional[str]:
        selectors = [
            "a[data-test-id='about-us__website'] span",
            ".org-about-us-company-module__website a",
            "a[href*='://'][target='_blank']",
        ]

        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get("href", "") if element.name == "a" else ""
                    text = element.get_text(strip=True)
                    if text and ("http" in text or "www" in text or ".com" in text):
                        return text
                    if href and "linkedin.com" not in href:
                        return href
            except Exception:
                continue

        return None

    def _extract_industry(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> Optional[str]:
        try:
            dt_elements = soup.find_all("dt")
            for dt in dt_elements:
                if "industry" in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        return dd.get_text(strip=True)
        except Exception:
            pass

        return None

    def _extract_follower_count(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> int:
        selectors = [
            ".org-top-card-summary-info-list__info-item",
            "span[class*='followers']",
            ".org-top-card-primary-actions__followers",
        ]

        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True).lower()
                    if "follower" in text:
                        return self._parse_follower_count(text)
            except Exception:
                continue

        return 0

    def _extract_headcount(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> Optional[str]:
        try:
            dt_elements = soup.find_all("dt")
            for dt in dt_elements:
                text = dt.get_text(strip=True).lower()
                if "company size" in text or "employees" in text:
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        return dd.get_text(strip=True)
        except Exception:
            pass

        return None

    def _extract_specialities(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> List[str]:
        specialities = []

        try:
            dt_elements = soup.find_all("dt")
            for dt in dt_elements:
                if "specialit" in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        text = dd.get_text(strip=True)
                        specialities = [s.strip() for s in text.split(",") if s.strip()]
                        break
        except Exception:
            pass

        return specialities

    def _extract_founded(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> Optional[str]:
        try:
            dt_elements = soup.find_all("dt")
            for dt in dt_elements:
                if "founded" in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        return dd.get_text(strip=True)
        except Exception:
            pass

        return None

    def _extract_headquarters(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> Optional[str]:
        try:
            dt_elements = soup.find_all("dt")
            for dt in dt_elements:
                text = dt.get_text(strip=True).lower()
                if "headquarters" in text or "location" in text:
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        return dd.get_text(strip=True)
        except Exception:
            pass

        return None

    def _extract_company_type(self, soup: BeautifulSoup, driver: webdriver.Chrome) -> Optional[str]:
        try:
            dt_elements = soup.find_all("dt")
            for dt in dt_elements:
                text = dt.get_text(strip=True).lower()
                if "type" in text:
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        return dd.get_text(strip=True)
        except Exception:
            pass

        return None

    async def scrape_posts(self, page_id: str, limit: int = 20) -> List[ScrapedPostData]:
        driver = self._get_driver()
        url = f"{self.BASE_URL}/{page_id}/posts/"
        posts = []

        try:
            driver.get(url)
            self._wait_for_page_load()
            time.sleep(2)

            scroll_count = min(limit // 5 + 1, 5)
            self._scroll_page(scroll_count=scroll_count, delay=1.5)

            soup = BeautifulSoup(driver.page_source, "lxml")
            post_containers = soup.select(".feed-shared-update-v2, .occludable-update")

            for idx, container in enumerate(post_containers[:limit]):
                try:
                    post_data = self._parse_post(container, page_id, idx)
                    if post_data:
                        posts.append(post_data)
                except Exception as e:
                    print(f"⚠️ Error parsing post {idx}: {str(e)}")
                    continue

        except TimeoutException:
            print(f"⏰ Timeout while loading posts: {url}")
        except Exception as e:
            print(f"❌ Error scraping posts for {page_id}: {str(e)}")

        return posts

    def _parse_post(self, container: BeautifulSoup, page_id: str, index: int) -> Optional[ScrapedPostData]:
        content_elem = container.select_one(
            ".feed-shared-update-v2__description, "
            ".feed-shared-text, "
            ".update-components-text"
        )
        content = content_elem.get_text(strip=True) if content_elem else None

        if not content:
            return None

        like_count = 0
        comment_count = 0
        share_count = 0

        social_counts = container.select(".social-details-social-counts span")
        for count_elem in social_counts:
            text = count_elem.get_text(strip=True).lower()
            count = self._parse_engagement_count(text)
            if "like" in text or "reaction" in text:
                like_count = count
            elif "comment" in text:
                comment_count = count
            elif "share" in text or "repost" in text:
                share_count = count

        media_url = None
        media_type = None

        img_elem = container.select_one(".feed-shared-image img, .update-components-image img")
        if img_elem:
            media_url = img_elem.get("src")
            media_type = "image"

        video_elem = container.select_one("video, .feed-shared-linkedin-video")
        if video_elem:
            media_url = video_elem.get("src") or video_elem.get("data-sources")
            media_type = "video"

        post_id = self._generate_post_id(page_id, content, index)

        return ScrapedPostData(
            post_id=post_id,
            page_id=page_id,
            content=content[:2000] if content else None,
            like_count=like_count,
            comment_count=comment_count,
            share_count=share_count,
            media_url=media_url,
            media_type=media_type,
            post_url=None,
            posted_at=None,
        )

    async def scrape_employees(self, page_id: str, limit: int = 20) -> List[ScrapedEmployeeData]:
        driver = self._get_driver()
        url = f"{self.BASE_URL}/{page_id}/people/"
        employees = []

        try:
            driver.get(url)
            self._wait_for_page_load()
            time.sleep(2)

            self._scroll_page(scroll_count=3, delay=1.5)

            soup = BeautifulSoup(driver.page_source, "lxml")
            employee_cards = soup.select(
                ".org-people-profile-card, "
                ".artdeco-entity-lockup, "
                ".org-people-profiles-module__profile-list li"
            )

            for card in employee_cards[:limit]:
                try:
                    employee_data = self._parse_employee(card, page_id)
                    if employee_data:
                        employees.append(employee_data)
                except Exception as e:
                    print(f"⚠️ Error parsing employee: {str(e)}")
                    continue

        except TimeoutException:
            print(f"⏰ Timeout while loading employees: {url}")
        except Exception as e:
            print(f"❌ Error scraping employees for {page_id}: {str(e)}")

        return employees

    def _parse_employee(self, card: BeautifulSoup, page_id: str) -> Optional[ScrapedEmployeeData]:
        name_elem = card.select_one(
            ".org-people-profile-card__profile-title, "
            ".artdeco-entity-lockup__title, "
            ".lt-line-clamp--single-line"
        )
        name = name_elem.get_text(strip=True) if name_elem else None

        if not name:
            return None

        designation_elem = card.select_one(
            ".artdeco-entity-lockup__subtitle, "
            ".org-people-profile-card__profile-info, "
            ".t-14"
        )
        designation = designation_elem.get_text(strip=True) if designation_elem else None

        location_elem = card.select_one(
            ".artdeco-entity-lockup__caption, "
            ".org-people-profile-card__location"
        )
        location = location_elem.get_text(strip=True) if location_elem else None

        profile_link = card.select_one("a[href*='/in/']")
        profile_url = profile_link.get("href") if profile_link else None
        if profile_url and not profile_url.startswith("http"):
            profile_url = f"https://www.linkedin.com{profile_url}"

        img_elem = card.select_one("img.EntityPhoto-circle-5, img[class*='profile']")
        profile_picture_url = img_elem.get("src") if img_elem else None

        return ScrapedEmployeeData(
            page_id=page_id,
            name=name,
            designation=designation,
            location=location,
            profile_url=profile_url,
            profile_picture_url=profile_picture_url,
        )

    async def scrape_comments(self, post_id: str, page_id: str, limit: int = 10) -> List[ScrapedCommentData]:
        return []

    async def scrape_all(self, page_id: str, posts_limit: int = 20, employees_limit: int = 20) -> Dict[str, Any]:
        try:
            page_data = await self.scrape_page(page_id)

            posts = []
            employees = []

            try:
                posts = await self.scrape_posts(page_id, limit=posts_limit)
            except Exception as e:
                print(f"⚠️ Could not scrape posts: {str(e)}")

            try:
                employees = await self.scrape_employees(page_id, limit=employees_limit)
            except Exception as e:
                print(f"⚠️ Could not scrape employees: {str(e)}")

            return {
                "page": page_data,
                "posts": posts,
                "employees": employees,
                "comments": [],
            }

        except (LoginWallException, ScrapingException):
            raise

        finally:
            self.close()
