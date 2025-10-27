// Elysia API server

import { jwt } from '@elysiajs/jwt';
import { and, eq, gt } from 'drizzle-orm';
import { Elysia, t } from 'elysia';
import { db } from './db';
import {
	LoginSchema,
	SafeUserResponseSchema,
	SignUpSchema,
	UserAddressResponseSchema,
	UserAddressSchema,
	UserResponseSchema,
	userAddressTable,
	usersTable,
} from './user.model';
import { comparePassword, hashPassword } from './utils/passwordHash';

const ErrorSchema = t.Object({
	message: t.String(),
});

if (!process.env.JWT_SECRET) {
	console.error('FATAL ERROR: JWT_SECRET is not defined in .env');
	process.exit(1);
}

export const usersPlugin = new Elysia({ prefix: '/api' })
	.decorate('db', db)
	.get('/', ({ path }) => path)
	.use(jwt({ name: 'jwt', secret: process.env.JWT_SECRET as string }))

	.group('/auth', (app) =>
		app
			.post(
				'/login',
				async ({ body, set, db, jwt, cookie }) => {
					const [userFromDb] = await db
						.select()
						.from(usersTable)
						.where(eq(usersTable.email, body.email));
					if (!userFromDb) {
						set.status = 401;
						return { message: 'Invalid email or password.' };
					}
					const passwordMatch = await comparePassword(userFromDb.password, body.password);
					if (!passwordMatch) {
						set.status = 401;
						return { message: 'Invalid email or password.' };
					}
					const userPayload = { id: userFromDb.id, email: userFromDb.email, role: userFromDb.role };
					const token = await jwt.sign(userPayload);

					cookie.auth?.set({
						value: token,
						path: '/',
						httpOnly: true,
						sameSite: 'lax',
						maxAge: 60 * 60 * 24 * 7, // 7 days
					});

					return { token };
				},
				{
					body: LoginSchema,
					response: {
						200: t.Object({ token: t.String() }),
						401: ErrorSchema,
					},
					detail: {
						tags: ['Authentication'],
						summary: 'Log in a user',
					},
				},
			)

			.post(
				'/logout',
				({ cookie, set }) => {
					const token = cookie?.auth?.value as string | undefined;

					if (!token) {
						set.status = 401;
						return { message: 'Unauthorized: No active session to log out from.' };
					}

					cookie.auth?.remove();
					return { ok: true };
				},
				{
					detail: {
						tags: ['Authentication'],
						summary: 'Log out the current user',
					},
					response: {
						200: t.Object({ ok: t.Boolean() }),
						401: ErrorSchema,
					},
				},
			),
	)

	.group('/users', (app) =>
		app

			.get('/offset', async ({ set, db, query }) => {
				const { offset, limit } = query;
				const userList = await db
					.select()
					.from(usersTable)
					.orderBy(usersTable.id)
					.limit(limit!)
					.offset(offset!);

				return { users: userList };
			}, {
				query: t.Object({
					offset: t.Number({ default: 0, minimum: 0 }), limit: t.Number({ default: 10, minimum: 1, maximum: 1000 })
				}),
				response: {
					200: t.Object({ users: t.Array(SafeUserResponseSchema) }),
				},
				detail: {
					tags: ['User Management'],
					summary: 'User pagination offset/limit',
				}
			})

			.get('/cursor', async ({ set, db, query }) => {
				const limit = 10;
				const cursor = query.cursor;

				const userList = await db
					.select()
					.from(usersTable)
					.orderBy(usersTable.id)
					.where(gt(usersTable.id, cursor))
					.limit(limit)

				return { users: userList };
			}, {
				query: t.Object({
					cursor: t.Number({ default: 0, minimum: 0 }), limit: t.Number({ default: 10, minimum: 1, maximum: 1000 })
				}),
				response: {
					200: t.Object({ users: t.Array(SafeUserResponseSchema) }),
				},
				detail: {
					tags: ['User Management'],
					summary: 'User pagination cursor-based',
				}
			})

			.get('/page', async ({ set, db, query }) => {
				const limit = query.per_page;
				const offset = (query.page - 1) * limit;

				const userList = await db
					.select()
					.from(usersTable)
					.orderBy(usersTable.id)
					.offset(offset)
					.limit(limit)

				return { users: userList };
			}, {
				query: t.Object({
					page: t.Number({ default: 1, minimum: 1 }), per_page: t.Number({ default: 10, minimum: 1, maximum: 1000 })
				}),
				response: {
					200: t.Object({ users: t.Array(SafeUserResponseSchema) }),
				},
				detail: {
					tags: ['User Management'],
					summary: 'User pagination page-based',
				}
			})

			.post(
				'/',
				async ({ body, set, db }) => {
					const existingEmail = await db
						.select()
						.from(usersTable)
						.where(eq(usersTable.email, body.email));
					if (existingEmail.length > 0) {
						set.status = 409;
						return { message: 'A user with this email already exists.' };
					}
					const existingUsername = await db
						.select()
						.from(usersTable)
						.where(eq(usersTable.username, body.username));
					if (existingUsername.length > 0) {
						set.status = 409;
						return { message: 'A user with this username already exists.' };
					}

					const hashedPassword = await hashPassword(body.password);
					const [newUser] = await db
						.insert(usersTable)
						.values({ ...body, password: hashedPassword })
						.returning();

					if (!newUser) {
						set.status = 500;
						return { message: 'Failed to create user account due to server error.' };
					}

					set.status = 201;
					return { user: newUser };
				},
				{
					body: t.Omit(SignUpSchema, ['id', 'role', 'created_at', 'updated_at']),
					response: {
						201: t.Object({ user: t.Omit(UserResponseSchema, ['password']) }),
						409: ErrorSchema,
						500: ErrorSchema,
					},
					detail: {
						tags: ['User Management'],
						summary: 'Register a new user',
					},
				},
			)

			.guard(
				{
					beforeHandle: async ({ jwt, set, cookie }) => {
						const token = cookie?.auth?.value as string | undefined;
						if (!token) {
							set.status = 401;
							return { message: 'Unauthorized: Missing token' };
						}
						const payload = await jwt.verify(token);
						if (!payload) {
							set.status = 401;
							return { message: 'Unauthorized: Invalid token' };
						}
					},
				},
				(app) =>
					app
						.resolve(async ({ jwt, cookie }) => {
							const token = cookie?.auth?.value as string | undefined;
							const userPayload = token
								? ((await jwt.verify(token)) as { id: number; email: string; role: string } | null)
								: null;
							return { user: userPayload };
						})

						.get(
							'/',
							async ({ db, set, user }) => {
								if (user?.role !== 'admin') {
									set.status = 403;
									return { message: 'Forbidden: Admins only' };
								}

								const allUsers = await db.select().from(usersTable);
								return { users: allUsers };
							},
							{
								response: {
									200: t.Object({ users: t.Array(SafeUserResponseSchema) }),
									403: ErrorSchema,
								},

								detail: {
									tags: ['User Management'],
									summary: 'Get all users (Admin Only)',
								},
							},
						)

						.get(
							'/me',
							async ({ user, set, db }) => {
								if (!user || typeof user.id !== 'number') {
									set.status = 401;
									return { message: 'Unauthorized' };
								}
								const [userFromDb] = await db
									.select()
									.from(usersTable)
									.where(eq(usersTable.id, user.id));
								if (!userFromDb) {
									set.status = 404;
									return { message: 'User not found' };
								}
								return { user: userFromDb };
							},
							{
								response: {
									200: t.Object({ user: t.Omit(UserResponseSchema, ['password']) }),
									401: ErrorSchema,
									404: ErrorSchema,
								},
								detail: {
									tags: ['User Management'],
									summary: 'Get current authenticated user',
								},
							},
						)

						.get(
							'/:id',
							async ({ params, set, db, user }) => {
								if (user?.role !== 'admin' && user?.id !== Number(params.id)) {
									set.status = 403;
									return {
										message:
											'Forbidden: Only admins or the user themselves can access this information',
									};
								}
								const uid = Number(params.id);
								const [existingUser] = await db
									.select()
									.from(usersTable)
									.where(eq(usersTable.id, uid));
								if (!existingUser) {
									set.status = 404;
									return { message: 'User not found.' };
								}
								return { user: existingUser };
							},
							{
								params: t.Object({ id: t.Number() }),
								response: {
									200: t.Object({ user: SafeUserResponseSchema }),
									403: ErrorSchema,
									404: ErrorSchema,
								},
								detail: {
									tags: ['User Management'],
									summary: 'Get user by ID',
								},
							},
						)

						.patch(
							'/:id',
							async ({ params, body, set, db, user }) => {
								if (user?.role !== 'admin' && user?.id !== Number(params.id)) {
									set.status = 403;
									return {
										message:
											'Forbidden: Only admins or the user themselves can update this information',
									};
								}
								const uid = Number(params.id);
								const [updatedUser] = await db
									.update(usersTable)
									.set(body)
									.where(eq(usersTable.id, uid))
									.returning();
								if (!updatedUser) {
									set.status = 404;
									return { message: 'User not found.' };
								}
								return { user: updatedUser };
							},
							{
								params: t.Object({ id: t.Number() }),
								body: t.Partial(
									t.Omit(SignUpSchema, ['id', 'password', 'role', 'created_at', 'updated_at']),
								),
								response: {
									200: t.Object({ user: SafeUserResponseSchema }),
									404: ErrorSchema,
								},
								detail: {
									tags: ['User Management'],
									summary: 'Partially update a user account information',
								},
							},
						)

						.delete(
							'/:id',
							async ({ params, set, db, user }) => {
								if (user?.role !== 'admin' && user?.id !== Number(params.id)) {
									set.status = 403;
									return {
										message:
											'Forbidden: Only admins or the user themselves can delete this account',
									};
								}

								const uid = Number(params.id);
								const [deletedUser] = await db
									.delete(usersTable)
									.where(eq(usersTable.id, uid))
									.returning();
								if (!deletedUser) {
									set.status = 404;
									return { message: 'User not found.' };
								}
								return { message: `User with ID ${uid} successfully deleted.` };
							},
							{
								params: t.Object({ id: t.Number() }),
								response: {
									200: t.Object({ message: t.String() }),
									404: ErrorSchema,
								},
								detail: {
									tags: ['User Management'],
									summary: 'Delete a user',
								},
							},
						)

						.post(
							'/:id/addresses',
							async ({ params, body, set, db, user }) => {
								if (user?.role !== 'admin' && user?.id !== Number(params.id)) {
									set.status = 403;
									return {
										message: 'Forbidden: Only admins or the user themselves can add addresses',
									};
								}

								const uid = Number(params.id);
								const [userFromDb] = await db
									.select()
									.from(usersTable)
									.where(eq(usersTable.id, uid));
								if (!userFromDb) {
									set.status = 404;
									return { message: 'User not found.' };
								}

								try {
									const [newAddress] = await db.transaction(async (tx) => {
										if (body.is_default === 1) {
											await tx
												.update(userAddressTable)
												.set({ is_default: 0 })
												.where(eq(userAddressTable.user_id, uid));
										}

										const [inserted] = await tx
											.insert(userAddressTable)
											.values({ ...body, user_id: uid })
											.returning();

										return [inserted];
									});

									if (!newAddress) throw new Error('Address creation failed within transaction.');

									set.status = 201;
									return { address: newAddress };
								} catch (error) {
									console.error('Transaction failed:', error);
									set.status = 500;
									return { message: 'Failed to add address due to a server error.' };
								}
							},
							{
								params: t.Object({ id: t.Number() }),
								body: t.Omit(UserAddressSchema, ['id', 'user_id']),
								response: {
									201: t.Object({ address: UserAddressResponseSchema }),
									403: ErrorSchema,
									404: ErrorSchema,
									500: ErrorSchema,
								},
								detail: {
									tags: ['User Management'],
									summary: 'Add a new address for a user',
								},
							},
						)

						.patch(
							'/:id/addresses/:address_id',
							async ({ params, body, set, db, user }) => {
								if (user?.role !== 'admin' && user?.id !== Number(params.id)) {
									set.status = 403;
									return {
										message: 'Forbidden: Only admins or the user themselves can update addresses',
									};
								}
								const uid = Number(params.id);
								const [userFromDb] = await db
									.select()
									.from(usersTable)
									.where(eq(usersTable.id, uid));
								if (!userFromDb) {
									set.status = 404;
									return { message: 'User not found.' };
								}
								try {
									const [updatedAddress] = await db.transaction(async (tx) => {
										if (body.is_default === 1) {
											await tx
												.update(userAddressTable)
												.set({ is_default: 0 })
												.where(eq(userAddressTable.user_id, uid));
										}

										const [result] = await tx
											.update(userAddressTable)
											.set(body)
											.where(
												and(
													eq(userAddressTable.id, params.address_id),
													eq(userAddressTable.user_id, uid),
												),
											)
											.returning();

										return [result];
									});

									if (!updatedAddress) {
										set.status = 404;
										return { message: 'Address not found.' };
									}

									return { address: updatedAddress };
								} catch (error) {
									console.error('Transaction failed:', error);
									set.status = 500;
									return { message: 'Failed to update address due to a server error.' };
								}
							},
							{
								params: t.Object({ id: t.Number(), address_id: t.Number() }),
								body: t.Partial(UserAddressSchema),
								response: {
									200: t.Object({ address: UserAddressResponseSchema }),
									403: ErrorSchema,
									404: ErrorSchema,
									500: ErrorSchema,
								},
								detail: {
									tags: ['User Management'],
									summary: 'Update an existing address for a user',
								},
							},
						),
			),
	);
