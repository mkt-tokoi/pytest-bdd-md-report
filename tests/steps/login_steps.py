from pytest_bdd import given, when, then
from playwright.sync_api import Page, expect

@given("ログインページを開いている")
def open_login_page(page: Page):
    page.goto("http://localhost:8000/login.html")

@when("正しいユーザー情報を入力する")
def input_credentials(page: Page):
    page.fill("#username", "testuser")
    page.fill("#password", "password")
    page.click("button[type=submit]")

@then("ダッシュボードが表示される")
def dashboard_is_visible(page: Page):
    expect(page.locator("h1")).to_have_text("Dashboard")

@then("失敗する")
def always_fail(page: Page):
    raise AssertionError("This step always fails")

