// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import {BaseStrategyInitializable, StrategyParams, SafeERC20, IERC20} from "@yearnV2/BaseStrategy.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";

import {IStrategy} from "@tokenized-strategy/interfaces/IStrategy.sol";

contract V3Router is BaseStrategyInitializable {
    using SafeERC20 for IERC20;

    IStrategy public strategy;
    uint256 public maxLoss;

    constructor(
        address _vault,
        address _strategy
    ) BaseStrategyInitializable(_vault) {
        initializeThis(_strategy);
    }

    function CloneV3Router(
        address _vault,
        address _strategy,
        address _strategist,
        address _rewards,
        address _keeper
    ) external returns (address _newV3Router) {
        _newV3Router = clone(_vault, _strategist, _rewards, _keeper);
        V3Router(_newV3Router).initializeThis(_strategy);
    }

    function initializeThis(address _strategy) public {
        require(address(strategy) == address(0), "!initiallized");
        require(IStrategy(_strategy).asset() == address(want), "wrong want");

        want.safeApprove(_strategy, type(uint256).max);
        strategy = IStrategy(_strategy);
        // Default to 1bps max loss
        maxLoss = 1;
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external view override returns (string memory) {
        return "V3 Router";
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return balanceOfWant() + balanceOfStrategy();
    }

    function balanceOfWant() public view returns (uint256) {
        return want.balanceOf(address(this));
    }

    function balanceOfStrategy() public view returns (uint256) {
        return strategy.convertToAssets(strategy.balanceOf(address(this)));
    }

    function prepareReturn(
        uint256 _debtOutstanding
    )
        internal
        override
        returns (uint256 _profit, uint256 _loss, uint256 _debtPayment)
    {
        // _totalInvested should account for all funds the strategy curently has
        uint256 totalAssets = estimatedTotalAssets();
        uint256 totalDebt = vault.strategies(address(this)).totalDebt;

        if (totalDebt < totalAssets) {
            // we have profit
            unchecked {
                _profit = totalAssets - totalDebt;
            }
        } else {
            // we have losses
            unchecked {
                _loss = totalDebt - totalAssets;
            }
        }

        (uint256 _amountFreed, ) = liquidatePosition(
            _debtOutstanding + _profit
        );

        _debtPayment = Math.min(_debtOutstanding, _amountFreed);

        //Adjust profit in case we had any losses from liquidatePosition
        _profit = _amountFreed - _debtPayment;
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        uint256 balance = balanceOfWant();
        if (balance > 0) {
            strategy.deposit(balance, address(this));
        }
    }

    function liquidatePosition(
        uint256 _amountNeeded
    ) internal override returns (uint256 _liquidatedAmount, uint256 _loss) {
        uint256 balance = balanceOfWant();

        if (_amountNeeded > balance) {
            strategy.withdraw(
                _amountNeeded - balance,
                address(this),
                address(this),
                maxLoss
            );
        }

        uint256 totalAssets = want.balanceOf(address(this));
        if (_amountNeeded > totalAssets) {
            _liquidatedAmount = totalAssets;
            unchecked {
                _loss = _amountNeeded - totalAssets;
            }
        } else {
            _liquidatedAmount = _amountNeeded;
        }
    }

    function liquidateAllPositions() internal override returns (uint256) {
        strategy.redeem(
            strategy.balanceOf(address(this)),
            address(this),
            address(this),
            maxLoss
        );

        return balanceOfWant();
    }

    function prepareMigration(address _newStrategy) internal override {
        strategy.transfer(_newStrategy, strategy.balanceOf(address(this)));
    }

    function setMaxLoss(uint256 _newMaxLoss) external onlyAuthorized {
        maxLoss = _newMaxLoss;
    }

    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}

    function ethToWant(
        uint256 _amtInWei
    ) public view virtual override returns (uint256) {
        // TODO create an accurate price oracle
        return _amtInWei;
    }
}
