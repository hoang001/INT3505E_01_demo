import { and, eq } from 'drizzle-orm';
import type { Static } from 'elysia';
import {
	ConflictError,
	InternalServerError,
	NotFoundError,
	UnauthorizedError,
} from '../common/errors/httpErrors';
import type { db as defaultDb } from './db';
import type { LoginSchema, SignUpSchema, UserAddressSchema } from './user.model';
import { userAddressTable, usersTable } from './user.model';
import { comparePassword, hashPassword } from './utils/passwordHash';

type DbClient = typeof defaultDb;
type JwtClient = {
	sign: (payload: Record<string, string | number>) => Promise<string>;
	verify: (token: string) => Promise<Record<string, string | number> | false>;
};

export class UserService {
	private db: DbClient;
	private jwt: JwtClient;

	constructor(db: DbClient, jwt: JwtClient) {
		this.db = db;
		this.jwt = jwt;
	}

	async login(credentials: Static<typeof LoginSchema>) {
		const [userFromDb] = await this.db
			.select()
			.from(usersTable)
			.where(eq(usersTable.email, credentials.email));

		if (!userFromDb) {
			throw new UnauthorizedError('Invalid email or password.');
		}

		const passwordMatch = await comparePassword(credentials.password, userFromDb.password);
		if (!passwordMatch) {
			throw new UnauthorizedError('Invalid email or password.');
		}

		const userPayload = { id: userFromDb.id, email: userFromDb.email, role: userFromDb.role };
		const token = await this.jwt.sign(userPayload);

		return { token };
	}

	async createUser(
		userData: Omit<Static<typeof SignUpSchema>, 'id' | 'role' | 'created_at' | 'updated_at'>,
	) {
		const existingEmail = await this.db
			.select()
			.from(usersTable)
			.where(eq(usersTable.email, userData.email));
		if (existingEmail.length > 0) {
			throw new ConflictError('A user with this email already exists.');
		}

		const existingUsername = await this.db
			.select()
			.from(usersTable)
			.where(eq(usersTable.username, userData.username));
		if (existingUsername.length > 0) {
			throw new ConflictError('A user with this username already exists.');
		}

		const hashedPassword = await hashPassword(userData.password);
		const [newUser] = await this.db
			.insert(usersTable)
			.values({ ...userData, password: hashedPassword })
			.returning();

		if (!newUser) {
			throw new InternalServerError('Failed to create user account due to server error.');
		}

		return newUser;
	}

	async getAllUsers() {
		const allUsers = await this.db.select().from(usersTable);
		return { users: allUsers };
	}

	async getUserById(id: number) {
		const [user] = await this.db.select().from(usersTable).where(eq(usersTable.id, id));
		if (!user) {
			throw new NotFoundError('User not found.');
		}
		return user;
	}

	async updateUser(id: number, userData: Partial<Static<typeof SignUpSchema>>) {
		const [updatedUser] = await this.db
			.update(usersTable)
			.set(userData)
			.where(eq(usersTable.id, id))
			.returning();

		if (!updatedUser) {
			throw new NotFoundError('User not found.');
		}
		return updatedUser;
	}

	async deleteUser(id: number) {
		const [deletedUser] = await this.db.delete(usersTable).where(eq(usersTable.id, id)).returning();
		if (!deletedUser) {
			throw new NotFoundError('User not found.');
		}
		return { message: `User with ID ${id} successfully deleted.` };
	}

	async addUserAddress(
		userId: number,
		addressData: Omit<Static<typeof UserAddressSchema>, 'id' | 'user_id'>,
	) {
		const [userFromDb] = await this.db.select().from(usersTable).where(eq(usersTable.id, userId));
		if (!userFromDb) {
			throw new NotFoundError('User not found.');
		}

		try {
			const [newAddress] = await this.db.transaction(async (tx) => {
				if (addressData.is_default === 1) {
					await tx
						.update(userAddressTable)
						.set({ is_default: 0 })
						.where(eq(userAddressTable.user_id, userId));
				}

				const [inserted] = await tx
					.insert(userAddressTable)
					.values({ ...addressData, user_id: userId })
					.returning();

				return [inserted];
			});

			if (!newAddress)
				throw new InternalServerError('Address creation failed within transaction.');

			return newAddress;
		} catch (error) {
			console.error('Transaction failed:', error);
			throw new InternalServerError('Failed to add address due to a server error.');
		}
	}

	async updateUserAddress(
		userId: number,
		addressId: number,
		addressData: Partial<Static<typeof UserAddressSchema>>,
	) {
		const [userFromDb] = await this.db.select().from(usersTable).where(eq(usersTable.id, userId));
		if (!userFromDb) {
			throw new NotFoundError('User not found.');
		}

		try {
			const [updatedAddress] = await this.db.transaction(async (tx) => {
				if (addressData.is_default === 1) {
					await tx
						.update(userAddressTable)
						.set({ is_default: 0 })
						.where(eq(userAddressTable.user_id, userId));
				}

				const [result] = await tx
					.update(userAddressTable)
					.set(addressData)
					.where(and(eq(userAddressTable.id, addressId), eq(userAddressTable.user_id, userId)))
					.returning();

				return [result];
			});

			if (!updatedAddress) {
				throw new NotFoundError('Address not found.');
			}

			return updatedAddress;
		} catch (error) {
			console.error('Transaction failed:', error);
			throw new InternalServerError('Failed to update address due to a server error.');
		}
	}
}
