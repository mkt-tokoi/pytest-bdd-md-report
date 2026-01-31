Feature: ログイン機能

  Scenario: 正常にログインできる
    Given ログインページを開いている
    When 正しいユーザー情報を入力する
    Then ダッシュボードが表示される
