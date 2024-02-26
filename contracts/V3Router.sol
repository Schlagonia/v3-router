// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
// V3 vault and strategy use the same relevant interface.
import {IStrategy} from "@tokenized-strategy/interfaces/IStrategy.sol";
// These are the core Yearn libraries
import {BaseStrategyInitializable, StrategyParams, SafeERC20, IERC20} from "@yearnV2/BaseStrategy.sol";

contract V3Router is BaseStrategyInitializable {
    using SafeERC20 for IERC20;

    // V3 vault to use.
    IStrategy public v3Vault;

    // Max loss for withdraws.
    uint256 public maxLoss;

    // Strategy specific name.
    string internal _name;

    constructor(
        address _vault,
        address _v3Vault,
        string memory name_
    ) BaseStrategyInitializable(_vault) {
        initializeThis(_v3Vault, name_);
    }

    function cloneV3Router(
        address _vault,
        address _v3Vault,
        string memory name_,
        address _strategist,
        address _rewards,
        address _keeper
    ) external returns (address _newV3Router) {
        _newV3Router = clone(_vault, _strategist, _rewards, _keeper);
        V3Router(_newV3Router).initializeThis(_v3Vault, name_);
    }

    function initializeThis(address _v3Vault, string memory name_) public {
        require(address(v3Vault) == address(0), "!initialized");
        require(IStrategy(_v3Vault).asset() == address(want), "wrong want");

        want.safeApprove(_v3Vault, type(uint256).max);
        v3Vault = IStrategy(_v3Vault);
        // Default to 1bps max loss
        maxLoss = 1;

        _name = name_;

        // Set health check
        healthCheck = 0xDDCea799fF1699e98EDF118e0629A974Df7DF012;
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external view override returns (string memory) {
        return _name;
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return balanceOfWant() + balanceOfVault();
    }

    function balanceOfWant() public view returns (uint256) {
        return want.balanceOf(address(this));
    }

    function balanceOfVault() public view returns (uint256) {
        return v3Vault.convertToAssets(v3Vault.balanceOf(address(this)));
    }

    function prepareReturn(
        uint256 _debtOutstanding
    )
        internal
        override
        returns (uint256 _profit, uint256 _loss, uint256 _debtPayment)
    {
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
        unchecked {
            _profit = _amountFreed - _debtPayment;
        }
    }

    function adjustPosition(uint256) internal override {
        uint256 balance = Math.min(
            balanceOfWant(),
            v3Vault.maxDeposit(address(this))
        );
        if (balance > 0) {
            v3Vault.deposit(balance, address(this));
        }
    }

    function liquidatePosition(
        uint256 _amountNeeded
    ) internal override returns (uint256 _liquidatedAmount, uint256 _loss) {
        uint256 balance = balanceOfWant();

        if (_amountNeeded > balance) {
            _amountNeeded = Math.min(
                _amountNeeded,
                v3Vault.convertToAssets(v3Vault.maxRedeem(address(this)))
            );

            v3Vault.redeem(
                v3Vault.convertToShares(_amountNeeded),
                address(this),
                address(this),
                maxLoss
            );
        }

        balance = balanceOfWant();
        if (_amountNeeded > balance) {
            _liquidatedAmount = balance;
            unchecked {
                _loss = _amountNeeded - balance;
            }
        } else {
            _liquidatedAmount = _amountNeeded;
        }
    }

    function liquidateAllPositions() internal override returns (uint256) {
        v3Vault.redeem(
            v3Vault.balanceOf(address(this)),
            address(this),
            address(this),
            maxLoss
        );

        return balanceOfWant();
    }

    function prepareMigration(address _newStrategy) internal override {
        uint256 balance = v3Vault.balanceOf(address(this));
        if (balance > 0) {
            v3Vault.transfer(_newStrategy, balance);
        }
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
        return _amtInWei;
    }
}
