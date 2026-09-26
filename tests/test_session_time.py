# tests/test_session_time.py

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.routes.session_service import (
    calculate_duration_hours,
    ensure_utc,
)


# ==========================================================
# ensure_utc
# ==========================================================


def test_ensure_utc_adds_utc_to_naive_datetime():
    """
    Datetime sem timezone deve ser interpretado como UTC.
    """

    value = datetime(2026, 1, 1, 12, 0, 0)

    result = ensure_utc(value)

    assert result.tzinfo == timezone.utc
    assert result == datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )


def test_ensure_utc_preserves_utc_datetime():
    """
    Datetime já em UTC deve permanecer equivalente.
    """

    value = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    result = ensure_utc(value)

    assert result == value
    assert result.tzinfo == timezone.utc


def test_ensure_utc_converts_other_timezone_to_utc():
    """
    Datetime com outro offset deve ser convertido para UTC.
    """

    offset = timezone(timedelta(hours=-3))

    value = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=offset,
    )

    result = ensure_utc(value)

    assert result == datetime(
        2026,
        1,
        1,
        15,
        0,
        0,
        tzinfo=timezone.utc,
    )


# ==========================================================
# calculate_duration_hours
# ==========================================================


def test_calculate_duration_one_hour_without_pause():
    """
    Uma hora bruta sem pausas deve resultar
    em uma hora líquida.
    """

    started_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    finished_at = started_at + timedelta(hours=1)

    result = calculate_duration_hours(
        started_at,
        finished_at,
        paused_seconds=0,
    )

    assert result == Decimal("1")


def test_calculate_duration_excludes_paused_time():
    """
    Dez minutos de pausa em uma sessão de uma hora
    devem resultar em cinquenta minutos ativos.
    """

    started_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    finished_at = started_at + timedelta(hours=1)

    result = calculate_duration_hours(
        started_at,
        finished_at,
        paused_seconds=600,
    )

    expected = Decimal(3000) / Decimal(3600)

    assert result == expected


def test_calculate_duration_uses_accumulated_paused_seconds():
    """
    O total acumulado de pausas deve ser descontado
    integralmente da duração bruta.
    """

    started_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    finished_at = started_at + timedelta(hours=2)

    # Três pausas acumuladas de 10 minutos.
    paused_seconds = 3 * 600

    result = calculate_duration_hours(
        started_at,
        finished_at,
        paused_seconds,
    )

    expected = Decimal(5400) / Decimal(3600)

    assert result == expected


def test_calculate_duration_zero_when_pause_equals_elapsed_time():
    """
    Se todo o período da sessão estiver contabilizado
    como pausa, a duração líquida deve ser zero.
    """

    started_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    finished_at = started_at + timedelta(minutes=30)

    result = calculate_duration_hours(
        started_at,
        finished_at,
        paused_seconds=1800,
    )

    assert result == Decimal("0")


def test_calculate_duration_never_returns_negative_value():
    """
    Pausas superiores ao tempo bruto não devem produzir
    duração líquida negativa.
    """

    started_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    finished_at = started_at + timedelta(minutes=30)

    result = calculate_duration_hours(
        started_at,
        finished_at,
        paused_seconds=3600,
    )

    assert result == Decimal("0")


def test_calculate_duration_accepts_naive_datetimes_as_utc():
    """
    Datetimes naive devem ser tratados como UTC,
    preservando compatibilidade com SQLite.
    """

    started_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
    )

    finished_at = datetime(
        2026,
        1,
        1,
        13,
        0,
        0,
    )

    result = calculate_duration_hours(
        started_at,
        finished_at,
        paused_seconds=0,
    )

    assert result == Decimal("1")


def test_calculate_duration_handles_different_timezones():
    """
    Instantes representados em timezones diferentes
    devem ser comparados corretamente em UTC.
    """

    utc_minus_three = timezone(timedelta(hours=-3))

    started_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=utc_minus_three,
    )

    finished_at = datetime(
        2026,
        1,
        1,
        16,
        0,
        0,
        tzinfo=timezone.utc,
    )

    result = calculate_duration_hours(
        started_at,
        finished_at,
        paused_seconds=0,
    )

    assert result == Decimal("1")


def test_session_time_with_multiple_pauses(
    db_session,
    test_user,
    monkeypatch,
):
    """
    Deve calcular corretamente o tempo líquido de uma sessão
    com múltiplos períodos de pausa.
    """

    from app.routes import session_service

    timeline = iter(
        [
            # start
            datetime(
                2026, 1, 1, 10, 0, 0,
                tzinfo=timezone.utc,
            ),
            # pause 1
            datetime(
                2026, 1, 1, 10, 30, 0,
                tzinfo=timezone.utc,
            ),
            # resume 1
            datetime(
                2026, 1, 1, 10, 40, 0,
                tzinfo=timezone.utc,
            ),
            # pause 2
            datetime(
                2026, 1, 1, 11, 0, 0,
                tzinfo=timezone.utc,
            ),
            # resume 2
            datetime(
                2026, 1, 1, 11, 5, 0,
                tzinfo=timezone.utc,
            ),
            # finish
            datetime(
                2026, 1, 1, 11, 30, 0,
                tzinfo=timezone.utc,
            ),
        ]
    )

    monkeypatch.setattr(
        session_service,
        "utc_now",
        lambda: next(timeline),
    )

    session = session_service.start_session(
        db=db_session,
        user_id=test_user.id,
        session_type="study",
    )

    assert ensure_utc(session.started_at) == datetime(
        2026, 1, 1, 10, 0, 0,
        tzinfo=timezone.utc,
    )

    session_service.pause_session(
        db=db_session,
        session_id=session.id,
        user_id=test_user.id,
    )

    session_service.resume_session(
        db=db_session,
        session_id=session.id,
        user_id=test_user.id,
    )

    assert session.paused_seconds == 600

    session_service.pause_session(
        db=db_session,
        session_id=session.id,
        user_id=test_user.id,
    )

    session_service.resume_session(
        db=db_session,
        session_id=session.id,
        user_id=test_user.id,
    )

    assert session.paused_seconds == 900

    session = session_service.finish_session(
        db=db_session,
        session_id=session.id,
        user_id=test_user.id,
    )

    assert session.status == "finished"
    assert session.paused_seconds == 900

    assert ensure_utc(session.finished_at) == datetime(
        2026, 1, 1, 11, 30, 0,
        tzinfo=timezone.utc,
    )

    assert session.duration_hours == Decimal("1.2500")


def test_finish_paused_session_counts_current_pause(
    db_session,
    test_user,
    monkeypatch,
):
    """
    Ao finalizar uma sessão pausada, o período de pausa
    ainda em andamento deve ser contabilizado.
    """

    from app.routes import session_service

    timeline = iter(
        [
            # start
            datetime(
                2026, 1, 1, 10, 0, 0,
                tzinfo=timezone.utc,
            ),
            # pause
            datetime(
                2026, 1, 1, 10, 30, 0,
                tzinfo=timezone.utc,
            ),
            # finish enquanto pausada
            datetime(
                2026, 1, 1, 10, 45, 0,
                tzinfo=timezone.utc,
            ),
        ]
    )

    monkeypatch.setattr(
        session_service,
        "utc_now",
        lambda: next(timeline),
    )

    session = session_service.start_session(
        db=db_session,
        user_id=test_user.id,
        session_type="study",
    )

    session_service.pause_session(
        db=db_session,
        session_id=session.id,
        user_id=test_user.id,
    )

    session = session_service.finish_session(
        db=db_session,
        session_id=session.id,
        user_id=test_user.id,
    )

    assert session.status == "finished"
    assert session.paused_at is None
    assert session.paused_seconds == 900

    assert ensure_utc(session.finished_at) == datetime(
        2026, 1, 1, 10, 45, 0,
        tzinfo=timezone.utc,
    )

    assert session.duration_hours == Decimal("0.5000")