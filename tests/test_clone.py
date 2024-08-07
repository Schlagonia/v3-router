import ape
from ape import Contract, project
import pytest


def clone_strategy(original, v3_vault, vault, strategist, rewards, keeper, gov):
    tx = original.cloneV3Router(
        vault, v3_vault, "test clone", strategist, rewards, keeper, sender=strategist
    )
    event = list(tx.decode_logs(original.Cloned))
    clone = project.V3Router.at(event[0].clone)
    vault.addStrategy(clone, 10_000, 0, 2**256 - 1, 0, sender=gov)
    return clone


def test_clone_operation(
    chain,
    accounts,
    token,
    vault,
    strategy,
    v3_vault,
    user,
    strategist,
    rewards,
    amount,
    RELATIVE_APPROX,
    keeper,
    gov,
):
    vault.updateStrategyDebtRatio(strategy, 0, sender=gov)
    strategy = clone_strategy(
        strategy, v3_vault, vault, strategist, rewards, keeper, gov
    )
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, sender=user)
    vault.deposit(amount, sender=user)
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.mine(1)
    strategy.harvest(sender=keeper)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # withdrawal
    vault.withdraw(sender=user)
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )


def test_emergency_exit(
    chain,
    accounts,
    gov,
    token,
    vault,
    strategy,
    v3_vault,
    user,
    strategist,
    amount,
    RELATIVE_APPROX,
    keeper,
    rewards,
):
    vault.updateStrategyDebtRatio(strategy, 0, sender=gov)
    strategy = clone_strategy(
        strategy, v3_vault, vault, strategist, rewards, keeper, gov
    )
    # Deposit to the vault
    token.approve(vault.address, amount, sender=user)
    vault.deposit(amount, sender=user)
    chain.mine(1)
    strategy.harvest(sender=keeper)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # set emergency and exit
    strategy.setEmergencyExit(sender=gov)
    chain.mine(1)
    strategy.harvest(sender=keeper)
    assert strategy.estimatedTotalAssets() < amount


def test_profitable_harvest(
    chain,
    accounts,
    token,
    vault,
    strategy,
    v3_vault,
    user,
    strategist,
    amount,
    whale,
    RELATIVE_APPROX,
    keeper,
    gov,
    rewards,
):
    vault.updateStrategyDebtRatio(strategy, 0, sender=gov)
    strategy = clone_strategy(
        strategy, v3_vault, vault, strategist, rewards, keeper, gov
    )
    # Deposit to the vault
    token.approve(vault.address, amount, sender=user)
    vault.deposit(amount, sender=user)
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds through the strategy
    chain.mine(1)
    strategy.harvest(sender=keeper)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    chain.mine(v3_vault.profitMaxUnlockTime())

    # Harvest 2: Realize profit
    chain.mine(1)
    before_pps = vault.pricePerShare()
    strategy.harvest(sender=keeper)
    chain.mine(3600 * 6)  # 6 hrs needed for profits to unlock
    chain.mine(1)
    profit = token.balanceOf(vault.address)  # Profits go to vault

    assert profit > 0
    assert token.balanceOf(strategy) == 0
    assert token.balanceOf(vault) == profit
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    assert v3_vault.totalAssets() > amount
    assert vault.pricePerShare() > before_pps


def test_change_debt(
    chain,
    gov,
    token,
    vault,
    strategy,
    v3_vault,
    user,
    strategist,
    amount,
    RELATIVE_APPROX,
    keeper,
    rewards,
):
    vault.updateStrategyDebtRatio(strategy, 0, sender=gov)
    strategy = clone_strategy(
        strategy, v3_vault, vault, strategist, rewards, keeper, gov
    )
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, sender=user)
    vault.deposit(amount, sender=user)
    vault.updateStrategyDebtRatio(strategy.address, 5_000, sender=gov)
    chain.mine(1)
    strategy.harvest(sender=keeper)
    half = int(amount / 2)

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 10_000, sender=gov)
    chain.mine(1)
    strategy.harvest(sender=keeper)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # In order to pass this tests, you will need to implement prepareReturn.
    vault.updateStrategyDebtRatio(strategy.address, 5_000, sender=gov)
    chain.mine(1)

    strategy.harvest(sender=keeper)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half


def test_sweep(
    gov,
    accounts,
    vault,
    strategy,
    v3_vault,
    strategist,
    rewards,
    keeper,
    token,
    user,
    amount,
):
    vault.updateStrategyDebtRatio(strategy, 0, sender=gov)
    strategy = clone_strategy(
        strategy, v3_vault, vault, strategist, rewards, keeper, gov
    )
    # Strategy want token doesn't work
    token.transfer(strategy, amount, sender=user)
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with ape.reverts("!want"):
        strategy.sweep(token, sender=gov)

    # Vault share token doesn't work
    with ape.reverts("!shares"):
        strategy.sweep(vault.address, sender=gov)

    # TODO: If you add protected tokens to the strategy.
    # Protected token doesn't work
    # with ape.reverts("!protected"):
    #     strategy.sweep(strategy.protectedToken(), sender=gov)

    to_sweep = Contract("0x514910771AF9Ca656af840dff83E8264EcF986CA")
    whale = accounts["0xF977814e90dA44bFA03b6295A0616a897441aceC"]
    amount = 100 * 10 ** to_sweep.decimals()
    before_balance = to_sweep.balanceOf(gov)
    to_sweep.transfer(strategy.address, amount, sender=whale)
    assert to_sweep.address != strategy.want()
    strategy.sweep(to_sweep, sender=gov)
    assert to_sweep.balanceOf(gov) == amount + before_balance


def test_triggers(
    chain,
    gov,
    vault,
    strategy,
    v3_vault,
    rewards,
    token,
    amount,
    user,
    weth,
    weth_amount,
    strategist,
    keeper,
):
    vault.updateStrategyDebtRatio(strategy, 0, sender=gov)
    strategy = clone_strategy(
        strategy, v3_vault, vault, strategist, rewards, keeper, gov
    )
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, sender=user)
    vault.deposit(amount, sender=user)
    vault.updateStrategyDebtRatio(strategy.address, 5_000, sender=gov)
    chain.mine(1)
    strategy.harvest(sender=keeper)

    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)
