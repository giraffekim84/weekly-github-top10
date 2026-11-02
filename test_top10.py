from top10 import build_message, parse


def art(repo, desc, stars):
    p = f'<p class="col-9">{desc}</p>' if desc else ""
    return (f'<article class="Box-row"><h2 class="h3"><a href="/{repo}" class="Link">x</a></h2>'
            f'{p}<span>{stars} stars this week</span></article>')


def test_parse_sorts_and_limits():
    page = "".join(art(f"o/r{i}", "d &amp; e", f"{i},000") for i in range(1, 13))
    page += '<article class="Box-row"><h2><a href="/o/nostars">x</a></h2></article>'
    top = parse(page)
    assert len(top) == 10
    assert top[0] == {"repo": "o/r12", "desc": "d & e", "stars": 12000}
    assert top[-1]["repo"] == "o/r3"


def test_message_ranks_10_to_1():
    msg = build_message(parse(art("a/big", "", "2,000") + art("b/small", "hi", "1,000")))
    assert msg.index("2위 small — hi (+1,000★)") < msg.index("1위 big (+2,000★)")
    assert "별 3,000개" in msg and "github.com/a/big" in msg


if __name__ == "__main__":
    test_parse_sorts_and_limits()
    test_message_ranks_10_to_1()
    print("ok")
