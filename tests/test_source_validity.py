import pytest

from xfetch.connectors.wechat import _looks_blocked
from xfetch.connectors.xiaohongshu import _extract_initial_state


def test_wechat_verification_page_is_not_content():
    assert _looks_blocked('<title>Weixin Official Accounts Platform</title><div>去验证</div>') is True


def test_xiaohongshu_login_wall_is_not_content():
    with pytest.raises(ValueError, match="login wall"):
        _extract_initial_state('<title>小红书 - 你的生活兴趣社区</title>登录后推荐更懂你的笔记')
